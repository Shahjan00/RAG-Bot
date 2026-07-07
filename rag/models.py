import uuid

from django.db import models


def generate_api_key():
    return uuid.uuid4().hex


class Business(models.Model):
    name = models.CharField(max_length=255)
    api_key = models.CharField(max_length=32, unique=True, default=generate_api_key, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Document(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField(max_length=255)
    uploaded_file = models.FileField(upload_to="documents/")
    extracted_text = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    chunk_index = models.PositiveIntegerField()
    chunk_text = models.TextField()
    embedding = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"
