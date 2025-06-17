from django.urls import path

from .views import ActivityListView, SubmitAnswerView

urlpatterns = [
    path("", ActivityListView.as_view(), name="activity-list"),
    path(
        "<int:activity_id>/submit/",
        SubmitAnswerView.as_view(),
        name="submit-answer",
    ),
]
