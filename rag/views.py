from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

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
                "message": "Document uploaded successfully.",
                "document_id": document.id,
                "business_id": document.business_id,
                "title": document.title,
                "chunk_count": document.chunks.count(),
            },
            status=status.HTTP_201_CREATED,
        )


class QuestionSearchView(APIView):
    def post(self, request):
        serializer = QuestionSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]
        top_k = serializer.validated_data["top_k"]
        matches = search_similar_chunks(question, limit=top_k)

        return Response(
            {
                "question": question,
                "match_count": len(matches),
                "results": matches,
            },
            status=status.HTTP_200_OK,
        )


class ChatView(APIView):
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]
        top_k = serializer.validated_data["top_k"]
        result = generate_chat_answer(question, top_k=top_k)

        return Response(result, status=status.HTTP_200_OK)
