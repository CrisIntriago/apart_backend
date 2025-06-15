from django.urls import path
from .views import ValidateAnswerView

urlpatterns = [
    path('validate/', ValidateAnswerView.as_view(), name='validate-answer'),
]
