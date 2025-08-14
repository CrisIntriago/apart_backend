from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from activities.models.base import Activity, UserAnswer
from content.models import Course, Module
from people.models import Student

FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", None)


class Command(BaseCommand):
    help = (
        "Envía emails a estudiantes con actividades pendientes en módulos que "
        "terminan dentro de la ventana dada (por end_date). Usa Student.course (FK)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=3,
            help="Ventana en días hacia adelante para módulos que terminan (default: 3)",  # noqa: E501
        )
        parser.add_argument(
            "--course-id",
            type=int,
            help="Opcional: limitar a un curso específico (ID)",
        )
        parser.add_argument(
            "--module-id",
            type=int,
            help="Opcional: limitar a un módulo específico (ID)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="No envía emails; solo imprime lo que se enviaría",
        )

    def handle(self, *args, **opts):
        days = opts["days"]
        now = timezone.now()
        until = now + timedelta(days=days)

        modules = Module.objects.filter(end_date__range=(now, until)).select_related(
            "course"
        )
        if opts.get("course_id"):
            modules = modules.filter(course_id=opts["course_id"])
        if opts.get("module_id"):
            modules = modules.filter(id=opts["module_id"])

        if not modules.exists():
            self.stdout.write(
                self.style.WARNING("No hay módulos por finalizar en el rango dado.")
            )
            return

        total_emails = 0

        for module in modules:
            course: Course = module.course

            students_qs = (
                Student.objects.filter(active_course=course)
                .select_related("person__user")
                .distinct()
            )

            if not students_qs.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"[{course.id}] {course} → sin estudiantes; se omite."
                    )
                )
                continue

            mod_activities = Activity.objects.filter(module=module)

            for student in students_qs:
                person = getattr(student, "person", None)
                user = getattr(person, "user", None) if person else None
                email = getattr(user, "email", None) if user else None
                first_name = (person.first_name if person else "") or (
                    user.username if user else "Estudiante"
                )

                if not user or not email:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Student {student.id} sin User/email; se omite."
                        )
                    )
                    continue

                answered_ids = UserAnswer.objects.filter(
                    user=user, activity__module=module
                ).values_list("activity_id", flat=True)

                pending_qs = mod_activities.exclude(id__in=answered_ids)

                if not pending_qs.exists():
                    continue

                subject = (
                    f"[{course}] Actividades pendientes del módulo “{module.name}”"
                )
                deadline_str = timezone.localtime(module.end_date).strftime(
                    "%d/%m/%Y %H:%M"
                )
                deadline_str = timezone.localtime(module.end_date).strftime(
                    "%d/%m/%Y %H:%M"
                )

                context = {
                    "first_name": first_name,
                    "course_name": str(course),
                    "module_name": module.name,
                    "deadline": deadline_str,
                    "module_url": getattr(module, "absolute_url", None),
                    "app_name": "Tu App",
                    "activities": [
                        {"title": a.title, "type_display": a.get_type_display()}
                        for a in pending_qs
                    ],
                }

                subject = (
                    f"[{course}] Actividades pendientes del módulo “{module.name}”"
                )
                text_body = render_to_string(
                    "emails/pending_module_activities.txt", context
                )
                html_body = render_to_string(
                    "emails/pending_module_activities.html", context
                )

                if opts["dry_run"]:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"[DRY-RUN] Para: {email}\nAsunto: {subject}\n\n{text_body}\n"  # noqa: E501
                        )
                    )
                else:
                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_body,
                        from_email=FROM_EMAIL,
                        to=[email],
                    )
                msg.attach_alternative(html_body, "text/html")
                msg.send(fail_silently=False)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Curso [{course.id}] “{course}” → módulo “{module.name}”: notificaciones procesadas."  # noqa: E501
                )
            )

        if opts["dry_run"]:
            self.stdout.write(
                self.style.NOTICE("DRY-RUN finalizado. No se enviaron correos.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Listo. Emails enviados: {total_emails}")
            )
