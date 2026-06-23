from django.urls import path

from .views import DocumentUploadView, QuestionSearchView


urlpatterns = [
    path("documents/upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("search/", QuestionSearchView.as_view(), name="question-search"),
]
