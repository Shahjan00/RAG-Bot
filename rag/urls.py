from django.urls import path

from .views import ChatView, DocumentUploadView, QuestionSearchView, WidgetSnippetView


urlpatterns = [
    path("documents/upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("search/", QuestionSearchView.as_view(), name="question-search"),
    path("chat/", ChatView.as_view(), name="chat"),
    path("widget/snippet/", WidgetSnippetView.as_view(), name="widget-snippet"),
]
