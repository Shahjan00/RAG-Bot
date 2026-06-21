from rest_framework import serializers

from .models import Document
from .utils import extract_text_from_pdf


class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "business", "title", "pdf_file", "extracted_text", "uploaded_at"]
        read_only_fields = ["id", "extracted_text", "uploaded_at"]

    def validate_pdf_file(self, value):
        file_name = value.name.lower()
        if not file_name.endswith(".pdf"):
            raise serializers.ValidationError("Only PDF files are allowed.")
        return value

    def create(self, validated_data):
        pdf_file = validated_data["pdf_file"]
        extracted_text = extract_text_from_pdf(pdf_file)
        validated_data["extracted_text"] = extracted_text
        pdf_file.seek(0)
        return Document.objects.create(**validated_data)
