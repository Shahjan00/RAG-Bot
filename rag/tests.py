from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import numpy as np

from rag.services.vector_store import build_faiss_index, search_similar_chunks


class FakeIndexFlatIP:
    def __init__(self, dimension):
        self.dimension = dimension
        self.vectors = None

    def add(self, matrix):
        self.vectors = matrix

    def search(self, query, limit):
        scores = np.dot(self.vectors, query[0])
        ranked_positions = np.argsort(scores)[::-1][:limit]
        return scores[ranked_positions].reshape(1, -1), ranked_positions.reshape(1, -1)


class FakeFaissModule:
    IndexFlatIP = FakeIndexFlatIP

    @staticmethod
    def normalize_L2(matrix):
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        matrix /= norms


class VectorStoreTests(TestCase):
    @patch("rag.services.vector_store.faiss", new=FakeFaissModule())
    @patch("rag.services.vector_store.generate_embedding", return_value=[1.0, 0.0])
    def test_search_returns_top_matching_chunks(self, _mock_generate_embedding):
        document = SimpleNamespace(id=10, title="Handbook")
        chunks = [
            SimpleNamespace(
                id=1,
                document=document,
                chunk_index=0,
                chunk_text="Alpha",
                embedding=[1.0, 0.0],
            ),
            SimpleNamespace(
                id=2,
                document=document,
                chunk_index=1,
                chunk_text="Beta",
                embedding=[0.0, 1.0],
            ),
        ]

        results = search_similar_chunks("What says alpha?", chunks=chunks)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["chunk_id"], 1)
        self.assertEqual(results[0]["chunk_text"], "Alpha")
        self.assertGreater(results[0]["score"], results[1]["score"])

    @patch("rag.services.vector_store.faiss", new=FakeFaissModule())
    def test_build_index_skips_invalid_embeddings(self):
        document = SimpleNamespace(id=11, title="Policy")
        chunks = [
            SimpleNamespace(
                id=1,
                document=document,
                chunk_index=0,
                chunk_text="Valid",
                embedding=[1.0, 0.0],
            ),
            SimpleNamespace(
                id=2,
                document=document,
                chunk_index=1,
                chunk_text="Missing",
                embedding=None,
            ),
            SimpleNamespace(
                id=3,
                document=document,
                chunk_index=2,
                chunk_text="Wrong shape",
                embedding=[1.0, 0.0, 3.0],
            ),
        ]

        index, indexed_chunks = build_faiss_index(chunks=chunks)

        self.assertIsNotNone(index)
        self.assertEqual(len(indexed_chunks), 1)
        self.assertEqual(indexed_chunks[0].chunk_text, "Valid")
