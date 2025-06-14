from django.urls import path

from .views import ActivityListView

urlpatterns = [
    path("list/", ActivityListView.as_view(), name="activity-list"),
]
