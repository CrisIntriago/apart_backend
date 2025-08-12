from django.urls import path

from .views import ActivityListView, LeaderboardTop10View, SubmitAnswerView

urlpatterns = [
    path("", ActivityListView.as_view(), name="activity-list"),
    path(
        "<int:activity_id>/submit/",
        SubmitAnswerView.as_view(),
        name="submit-answer",
    ),
    path(
        "leaderboard/top10/", LeaderboardTop10View.as_view(), name="leaderboard-top10"
    ),
]
