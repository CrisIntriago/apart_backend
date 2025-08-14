from django.db import models as dj_models
from django.utils import timezone

from .models import EnrollmentStatus, Student


def sync_active_course(student: Student):
    now = timezone.now()
    qs = student.enrollments.filter(status=EnrollmentStatus.ACTIVE).filter(
        dj_models.Q(start_at__isnull=True) | dj_models.Q(start_at__lte=now),
        dj_models.Q(end_at__isnull=True) | dj_models.Q(end_at__gte=now),
    )

    count = qs.count()
    if count == 1:
        enrollment = qs.first()
        if student.active_course_id != enrollment.course_id:
            student.active_course = enrollment.course
            student.save(update_fields=["active_course"])
    elif count == 0:
        if student.active_course_id is not None:
            student.active_course = None
            student.save(update_fields=["active_course"])
