from rest_framework import serializers

from .models import Document, DocumentChunk
from .services.embedding import generate_embedding
from .services.rag_pipeline import (
    chunk_text,
    extract_text_from_file,
    get_allowed_extensions_text,
    is_supported_file,
)


class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "business", "title", "uploaded_file", "extracted_text", "uploaded_at"]
        read_only_fields = ["id", "extracted_text", "uploaded_at"]

    def validate_uploaded_file(self, value):
        if not is_supported_file(value.name):
            raise serializers.ValidationError(
                f"Unsupported file type. Allowed types: {get_allowed_extensions_text()}."
            )
        return value

    def create(self, validated_data):
        document = Document.objects.create(extracted_text="", **validated_data)

        try:
            document.extracted_text = extract_text_from_file(document.uploaded_file.path)
            document.save(update_fields=["extracted_text"])

            chunks = chunk_text(document.extracted_text, chunk_size=500, overlap=50)
            for index, chunk in enumerate(chunks):
                DocumentChunk.objects.create(
                    document=document,
                    chunk_index=index,
                    chunk_text=chunk,
                    embedding=generate_embedding(chunk),
                )
        except Exception as exc:
            document.uploaded_file.delete(save=False)
            document.delete()
            raise serializers.ValidationError(
                {"uploaded_file": f"Could not extract text from this file. {exc}"}
            )

        return document


class QuestionSearchSerializer(serializers.Serializer):
    question = serializers.CharField()
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=20, default=5)


class ChatRequestSerializer(serializers.Serializer):
    question = serializers.CharField()
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=20, default=5)
