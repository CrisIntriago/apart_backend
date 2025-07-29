from django.urls import path

from .views import CourseListView, CourseModuleActivitiesView, CourseModulesView, CourseStudentsView

urlpatterns = [
    path("courses/", CourseListView.as_view(), name="course-list"),
    path(
        "courses/<int:pk>/modules/", CourseModulesView.as_view(), name="course-modules"
    ),
    path(
        "courses/<int:pk>/students/",
        CourseStudentsView.as_view(),
        name="course-students",
    ),
    path(
        "courses/<int:pk>/modules/<int:module_pk>/activities/",
        CourseModuleActivitiesView.as_view(),
        name="course-module-activities",
    ),
]
