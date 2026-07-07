from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch

import numpy as np
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory

from rag.services.ai_insights import build_chat_prompt, generate_chat_answer
from rag.services.vector_store import _get_chunk_source, build_faiss_index, search_similar_chunks
from rag.views import ChatView, QuestionSearchView, WidgetSnippetView


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

    @patch("rag.services.vector_store.DocumentChunk.objects")
    def test_get_chunk_source_filters_by_business(self, mock_objects):
        business = SimpleNamespace(id=7)
        ordered_queryset = MagicMock()
        filtered_queryset = MagicMock()

        mock_objects.select_related.return_value.order_by.return_value = ordered_queryset
        ordered_queryset.filter.return_value = filtered_queryset

        result = _get_chunk_source(business=business)

        ordered_queryset.filter.assert_called_once_with(document__business=business)
        self.assertEqual(result, filtered_queryset)


class ChatFlowTests(SimpleTestCase):
    def test_build_chat_prompt_includes_question_and_context(self):
        chunks = [
            {
                "document_title": "Policy.pdf",
                "chunk_index": 0,
                "chunk_text": "Refunds are allowed within 30 days.",
            }
        ]

        prompt = build_chat_prompt("What is the refund policy?", chunks)

        self.assertIn("Question: What is the refund policy?", prompt)
        self.assertIn("Document: Policy.pdf", prompt)
        self.assertIn("Refunds are allowed within 30 days.", prompt)

    @patch("rag.services.ai_insights.search_similar_chunks")
    @patch("rag.services.ai_insights.OpenAI")
    def test_generate_chat_answer_uses_retrieved_chunks(self, mock_openai_class, mock_search):
        business = SimpleNamespace(id=2)
        mock_search.return_value = [
            {
                "chunk_id": 1,
                "document_id": 2,
                "document_title": "Policy.pdf",
                "chunk_index": 0,
                "chunk_text": "Refunds are allowed within 30 days.",
                "score": 0.95,
            }
        ]
        mock_client = mock_openai_class.return_value
        mock_client.responses.create.return_value = SimpleNamespace(
            output_text="The refund policy allows refunds within 30 days."
        )

        result = generate_chat_answer("What is the refund policy?", business=business)

        self.assertEqual(
            result["answer"],
            "The refund policy allows refunds within 30 days.",
        )
        self.assertEqual(result["match_count"], 1)
        self.assertEqual(result["results"][0]["chunk_id"], 1)
        mock_search.assert_called_once_with(
            "What is the refund policy?",
            limit=5,
            business=business,
        )

    @patch("rag.views.generate_chat_answer")
    @patch("rag.views.get_request_business")
    def test_chat_view_returns_answer(self, mock_get_request_business, mock_generate_chat_answer):
        mock_get_request_business.return_value = SimpleNamespace(id=2)
        mock_generate_chat_answer.return_value = {
            "question": "What is the refund policy?",
            "answer": "Refunds are allowed within 30 days.",
            "match_count": 1,
            "results": [
                {
                    "chunk_id": 1,
                    "document_id": 2,
                    "document_title": "Policy.pdf",
                    "chunk_index": 0,
                    "chunk_text": "Refunds are allowed within 30 days.",
                    "score": 0.95,
                }
            ],
        }
        request = APIRequestFactory().post(
            "/api/chat/",
            {"question": "What is the refund policy?"},
            format="json",
        )

        response = ChatView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["answer"], "Refunds are allowed within 30 days.")
        self.assertEqual(response.data["business_id"], 2)

    def test_search_view_requires_api_key(self):
        request = APIRequestFactory().post(
            "/api/search/",
            {"question": "What is the refund policy?"},
            format="json",
        )

        response = QuestionSearchView.as_view()(request)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "Valid X-API-Key header is required.")

    @override_settings(ALLOWED_HOSTS=["testserver"])
    @patch("rag.views.get_request_business")
    def test_widget_snippet_view_returns_script_tag(self, mock_get_request_business):
        mock_get_request_business.return_value = SimpleNamespace(id=2, api_key="abc123")
        request = APIRequestFactory().get("/api/widget/snippet/")

        response = WidgetSnippetView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("<script", response.data["script_tag"])
        self.assertIn('data-api-key="abc123"', response.data["script_tag"])

    @patch("rag.views.get_request_business")
    @patch("rag.views.generate_chat_answer")
    def test_chat_view_adds_cors_header(self, mock_generate_chat_answer, mock_get_request_business):
        mock_get_request_business.return_value = SimpleNamespace(id=2)
        mock_generate_chat_answer.return_value = {
            "question": "Hello",
            "answer": "Hi",
            "match_count": 0,
            "results": [],
        }
        request = APIRequestFactory().post(
            "/api/chat/",
            {"question": "Hello", "api_key": "abc123"},
            format="json",
        )

        response = ChatView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], "*")
