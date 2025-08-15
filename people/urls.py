from django.urls import path

from .views import (
    MyCoursesProgressView,
    MyVocabularyView,
    StudentProfileView,
    UpdateAccessView,
)

urlpatterns = [
    path("profile/", StudentProfileView.as_view(), name="student_profile"),
    path(
        "courses/progress/",
        MyCoursesProgressView.as_view(),
        name="my_courses_progress",
    ),
    path("vocabulary/", MyVocabularyView.as_view(), name="my_vocabulary"),
    path("update-access/", UpdateAccessView.as_view(), name="update_access"),
]
