from django.urls import path
from .views import CourseListView, CourseModulesView

urlpatterns = [
    path('courses/', CourseListView.as_view(), name='course-list'),
    path('courses/<int:pk>/modules/', CourseModulesView.as_view(), name='course-modules'),
]
