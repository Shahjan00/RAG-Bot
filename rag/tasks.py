from celery import shared_task

from .models import Document, DocumentChunk
from .services.embedding import generate_embedding
from .services.rag_pipeline import chunk_text, extract_text_from_file


@shared_task
def process_document_upload(document_id):
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return

    document.processing_status = Document.STATUS_PROCESSING
    document.processing_error = ""
    document.save(update_fields=["processing_status", "processing_error"])

    try:
        extracted_text = extract_text_from_file(document.uploaded_file.path)
        document.extracted_text = extracted_text
        document.processing_status = Document.STATUS_COMPLETED
        document.save(update_fields=["extracted_text", "processing_status"])

        document.chunks.all().delete()
        chunks = chunk_text(extracted_text, chunk_size=500, overlap=50)
        for index, chunk in enumerate(chunks):
            DocumentChunk.objects.create(
                document=document,
                chunk_index=index,
                chunk_text=chunk,
                embedding=generate_embedding(chunk),
            )
    except Exception as exc:
        document.processing_status = Document.STATUS_FAILED
        document.processing_error = str(exc)
        document.save(update_fields=["processing_status", "processing_error"])
