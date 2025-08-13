# content/permissions.py
from rest_framework.permissions import BasePermission

from .models import ExamAttempt, ExamAttemptStatus


class HasStartedExam(BasePermission):
    """
    Permite acceso solo si existe un intento IN_PROGRESS del usuario sobre el examen
    y no está expirado.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        attempt = (
            ExamAttempt.objects.filter(
                exam=obj, user=request.user, status=ExamAttemptStatus.IN_PROGRESS
            )
            .order_by("-started_at")
            .first()
        )
        if not attempt:
            return False
        if attempt.is_expired():
            return False
        return True
