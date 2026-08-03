from __future__ import annotations

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context with grounded citations.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở tri thức."

        context_parts = []
        for idx, r in enumerate(results, start=1):
            content = r.get("content", "")
            meta = r.get("metadata", {})
            source = meta.get("source") or meta.get("doc_id") or r.get("doc_id") or r.get("id") or f"doc_{idx}"
            context_parts.append(f"[{idx}] (Nguồn: {source})\n{content}")

        context_str = "\n\n".join(context_parts)
        prompt = (
            "Instruction: Sử dụng CHỈ các thông tin trong phần Context dưới đây để trả lời câu hỏi. "
            "Nếu thông tin trong Context không đủ để trả lời, hãy nói rõ là thông tin không đủ.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )
        return self.llm_fn(prompt)


