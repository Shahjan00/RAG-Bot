from django.conf import settings

from openai import OpenAI

from rag.services.vector_store import search_similar_chunks


def build_chat_prompt(question, chunks):
    if not chunks:
        context_text = "No relevant document chunks were found."
    else:
        context_parts = []
        for chunk in chunks:
            context_parts.append(
                f"Document: {chunk['document_title']}\n"
                f"Chunk #{chunk['chunk_index']}\n"
                f"Content: {chunk['chunk_text']}"
            )
        context_text = "\n\n".join(context_parts)

    return (
        "You are a helpful assistant for question answering over business documents.\n"
        "Answer the question using only the context below.\n"
        "If the context does not contain the answer, say you do not know.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question: {question}"
    )


def generate_chat_answer(question, top_k=5):
    chunks = search_similar_chunks(question, limit=top_k)
    prompt = build_chat_prompt(question, chunks)

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.responses.create(
        model=settings.OPENAI_CHAT_MODEL,
        input=prompt,
    )

    return {
        "question": question,
        "answer": response.output_text,
        "match_count": len(chunks),
        "results": chunks,
    }
