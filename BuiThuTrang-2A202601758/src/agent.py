from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy ngữ cảnh phù hợp để trả lời."
        context = "\n".join(
            f"[{index}] ({result['metadata'].get('doc_id', result['id'])}) {result['content']}"
            for index, result in enumerate(results, 1)
        )
        return self.llm_fn(
            "Chỉ trả lời dựa trên context dưới đây; nói rõ nếu context không đủ.\n"
            f"Context:\n{context}\nQuestion: {question}\nAnswer:"
        )
