from django.urls import path

from .views import (
    CourseExamsView,
    CourseListView,
    CourseModuleActivitiesView,
    CourseModulesView,
    CourseProgressView,
    CourseStudentsView,
    ExamActivitiesView,
    FinishAttemptAndSubmitAnswersView,
    StartAttemptView,
)

urlpatterns = [
    path("courses/", CourseListView.as_view(), name="course-list"),
    path(
        "courses/<int:course_id>/progress/",
        CourseProgressView.as_view(),
        name="course-progress",
    ),
    path(
        "courses/<int:pk>/modules/", CourseModulesView.as_view(), name="course-modules"
    ),
    path(
        "courses/<int:pk>/students/",
        CourseStudentsView.as_view(),
        name="course-students",
    ),
    path("courses/<int:pk>/exams/", CourseExamsView.as_view(), name="course-exams"),
    path(
        "courses/<int:pk>/modules/<int:module_pk>/activities/",
        CourseModuleActivitiesView.as_view(),
        name="course-module-activities",
    ),
    path("exams/<int:exam_id>/start/", StartAttemptView.as_view(), name="exam-start"),
    path(
        "exams/<int:exam_id>/activities/",
        ExamActivitiesView.as_view(),
        name="exam-activities",
    ),
    path(
        "exams/<int:exam_id>/finish/",
        FinishAttemptAndSubmitAnswersView.as_view(),
        name="exam-finish",
    ),
]
