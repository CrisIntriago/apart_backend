from django.urls import path

from .views import MyVocabularyView, StudentProfileView

urlpatterns = [
    path("profile/", StudentProfileView.as_view(), name="student_profile"),
    path("vocabulary/", MyVocabularyView.as_view(), name="my_vocabulary"),
]
