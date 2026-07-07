from django.templatetags.static import static
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Business
from .serializers import (
    ChatRequestSerializer,
    DocumentUploadSerializer,
    QuestionSearchSerializer,
)
from .services.ai_insights import generate_chat_answer
from .services.vector_store import search_similar_chunks


class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()

        return Response(
            {
                "message": "Document uploaded. Processing started in background.",
                "document_id": document.id,
                "business_id": document.business_id,
                "title": document.title,
                "processing_status": document.processing_status,
            },
            status=status.HTTP_202_ACCEPTED,
        )


def get_request_business(request):
    api_key = request.headers.get("X-API-Key", "").strip()
    if not api_key:
        api_key = str(request.data.get("api_key", "")).strip()
    if not api_key:
        return None

    return Business.objects.filter(api_key=api_key).first()


def add_widget_cors_headers(response):
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
    return response


class QuestionSearchView(APIView):
    def post(self, request):
        business = get_request_business(request)
        if business is None:
            return Response(
                {"detail": "Valid X-API-Key header is required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = QuestionSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]
        top_k = serializer.validated_data["top_k"]
        matches = search_similar_chunks(question, limit=top_k, business=business)

        return Response(
            {
                "business_id": business.id,
                "question": question,
                "match_count": len(matches),
                "results": matches,
            },
            status=status.HTTP_200_OK,
        )


class ChatView(APIView):
    def options(self, request):
        response = Response(status=status.HTTP_200_OK)
        return add_widget_cors_headers(response)

    def post(self, request):
        business = get_request_business(request)
        if business is None:
            response = Response(
                {"detail": "Valid X-API-Key header is required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            return add_widget_cors_headers(response)

        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]
        top_k = serializer.validated_data["top_k"]
        result = generate_chat_answer(question, business=business, top_k=top_k)
        result["business_id"] = business.id

        response = Response(result, status=status.HTTP_200_OK)
        return add_widget_cors_headers(response)


class WidgetSnippetView(APIView):
    def get(self, request):
        business = get_request_business(request)
        if business is None:
            return Response(
                {"detail": "Valid X-API-Key header is required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        widget_script_url = request.build_absolute_uri(static("rag/chat-widget.js"))
        chat_api_url = request.build_absolute_uri("/api/chat/")
        script_tag = (
            f'<script src="{widget_script_url}" '
            f'data-api-key="{business.api_key}" '
            f'data-chat-url="{chat_api_url}"></script>'
        )

        return Response(
            {
                "business_id": business.id,
                "script_tag": script_tag,
            },
            status=status.HTTP_200_OK,
        )
