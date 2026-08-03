from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Uses an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

    def _make_record(self, doc: Document) -> dict[str, Any]:
        emb = self._embedding_fn(doc.content)
        meta = dict(doc.metadata) if doc.metadata else {}
        doc_id = meta.get("doc_id", doc.id)
        meta["doc_id"] = doc_id
        self._next_index += 1
        chunk_id = doc.id if "::chunk_" in doc.id else f"{doc.id}_{self._next_index}"
        return {
            "id": chunk_id,
            "doc_id": doc_id,
            "content": doc.content,
            "metadata": meta,
            "embedding": emb,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records:
            return []
        query_emb = self._embedding_fn(query)
        scored = []
        for r in records:
            score = _dot(query_emb, r["embedding"])
            record_copy = dict(r)
            record_copy["score"] = float(score)
            scored.append(record_copy)
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it in-memory.
        """
        if not docs:
            return
        for doc in docs:
            rec = self._make_record(doc)
            self._store.append(rec)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict | None = None) -> list[dict[str, Any]]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        candidates = []
        for r in self._store:
            r_meta = r.get("metadata", {})
            match = True
            for k, v in metadata_filter.items():
                if r_meta.get(k) != v:
                    match = False
                    break
            if match:
                candidates.append(r)

        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        initial_len = len(self._store)
        self._store = [
            r
            for r in self._store
            if not (
                r.get("doc_id") == doc_id
                or r.get("id") == doc_id
                or r.get("metadata", {}).get("doc_id") == doc_id
                or str(r.get("id", "")).startswith(f"{doc_id}_")
                or str(r.get("id", "")).startswith(f"{doc_id}::")
            )
        ]
        return len(self._store) < initial_len


