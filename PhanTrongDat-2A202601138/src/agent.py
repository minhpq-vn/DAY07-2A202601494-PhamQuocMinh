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
        if self.store.get_collection_size() == 0:
            return "Knowledge base is empty."

        results = self.store.search(question, top_k=top_k)
        if not results:
            return "No relevant context found."

        context_parts = []
        for index, res in enumerate(results, start=1):
            doc_id = res.get("metadata", {}).get("doc_id", res.get("id", f"doc_{index}"))
            context_parts.append(f"[{index}] ({doc_id}) {res['content']}")

        context_str = "\n".join(context_parts)

        prompt = (
            "Instruction: Answer the question using only the context provided. Say clearly if context is insufficient.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
