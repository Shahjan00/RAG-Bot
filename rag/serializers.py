from django.db import transaction
from rest_framework import serializers

from .models import Document
from .services.rag_pipeline import get_allowed_extensions_text, is_supported_file
from .tasks import process_document_upload


class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "business",
            "title",
            "uploaded_file",
            "extracted_text",
            "processing_status",
            "processing_error",
            "uploaded_at",
        ]
        read_only_fields = ["id", "extracted_text", "processing_status", "processing_error", "uploaded_at"]

    def validate_uploaded_file(self, value):
        if not is_supported_file(value.name):
            raise serializers.ValidationError(
                f"Unsupported file type. Allowed types: {get_allowed_extensions_text()}."
            )
        return value

    def create(self, validated_data):
        document = Document.objects.create(
            extracted_text="",
            processing_status=Document.STATUS_PENDING,
            processing_error="",
            **validated_data,
        )
        transaction.on_commit(lambda: process_document_upload.delay(document.id))
        return document


class QuestionSearchSerializer(serializers.Serializer):
    question = serializers.CharField()
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=20, default=5)


class ChatRequestSerializer(serializers.Serializer):
    question = serializers.CharField()
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=20, default=5)
