from types import SimpleNamespace

import numpy as np

from rag.models import DocumentChunk
from rag.services.embedding import generate_embedding

try:
    import faiss
except ImportError:  # pragma: no cover - depends on environment setup
    faiss = None


def _require_faiss():
    if faiss is None:
        raise ImportError(
            "faiss is not installed. Add faiss-cpu to requirements and install dependencies."
        )


def _normalize_embedding(embedding):
    if not embedding:
        return None

    vector = np.asarray(embedding, dtype="float32")
    if vector.ndim != 1 or vector.size == 0:
        return None

    return vector


def _get_chunk_source(chunks=None, business=None):
    if chunks is not None:
        return chunks

    queryset = DocumentChunk.objects.select_related("document").order_by("id")

    if business is not None:
        queryset = queryset.filter(document__business=business)

    return queryset


def build_faiss_index(chunks=None, business=None):
    _require_faiss()

    valid_chunks = []
    vectors = []
    dimension = None

    for chunk in _get_chunk_source(chunks=chunks, business=business):
        vector = _normalize_embedding(getattr(chunk, "embedding", None))
        if vector is None:
            continue

        if dimension is None:
            dimension = vector.shape[0]

        if vector.shape[0] != dimension:
            continue

        valid_chunks.append(chunk)
        vectors.append(vector)

    if not vectors:
        return None, []

    matrix = np.vstack(vectors)
    faiss.normalize_L2(matrix)

    index = faiss.IndexFlatIP(dimension)
    index.add(matrix)

    return index, valid_chunks


def search_similar_chunks(question, limit=5, chunks=None, business=None):
    _require_faiss()

    index, indexed_chunks = build_faiss_index(chunks=chunks, business=business)
    if index is None:
        return []

    question_vector = _normalize_embedding(generate_embedding(question))
    if question_vector is None:
        return []

    query = question_vector.reshape(1, -1)
    faiss.normalize_L2(query)

    result_count = min(limit, len(indexed_chunks))
    scores, positions = index.search(query, result_count)

    matches = []
    for score, position in zip(scores[0], positions[0]):
        if position < 0:
            continue

        chunk = indexed_chunks[position]
        document = getattr(chunk, "document", None) or SimpleNamespace(title="", id=None)
        matches.append(
            {
                "chunk_id": chunk.id,
                "document_id": document.id,
                "document_title": document.title,
                "chunk_index": chunk.chunk_index,
                "chunk_text": chunk.chunk_text,
                "score": float(score),
            }
        )

    return matches
