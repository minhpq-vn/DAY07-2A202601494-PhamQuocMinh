from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

from ingest import build_knowledge_base
from src import KnowledgeBaseAgent, RecursiveChunker, _mock_embed


QUERIES = [
    ("số liệu", "How long is the minimum legal guarantee for faulty goods?", "Two years from receipt of the goods.", "eu-guarantees-returns", "minimum legal guarantee lasts two years", {"customer_role": "buyer"}),
    ("điều kiện", "When can a buyer receive a refund instead of repair or replacement?", "When repair or replacement is impossible or cannot be completed reasonably without significant inconvenience.", "eu-guarantees-returns", "within a reasonable time and without significant inconvenience", {"customer_role": "buyer"}),
    ("quy trình", "What must an online seller do before charging an extra payment at checkout?", "Disclose accepted methods and total costs, then obtain explicit consent for the extra payment.", "eu-online-shop-rules", "extra payments require explicit customer consent", {"customer_role": "seller"}),
    ("liệt kê", "Which product problems allow a customer to claim redress from a seller?", "Mismatch with description or advertising, unfitness for purpose, abnormal quality/performance, or incorrect installation.", "eu-seller-guarantees", "does not match its description", {"customer_role": "seller"}),
    ("ngoại lệ", "Can an online customer return clearly personalised goods during the cooling-off period?", "No. Clearly personalised goods are exempt from the general fourteen-day cooling-off period.", "eu-shopping-rights", "personalised goods", {"customer_role": "buyer"}),
]


class HeadingChunker:
    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        chunks: list[str] = []
        sections = filter(None, (part.strip() for part in re.split(r"(?m)(?=^#{1,6}\s+)", text)))
        for section in sections:
            lines = section.splitlines()
            heading = lines[0] if lines[0].startswith("#") else ""
            if len(section) <= self.chunk_size:
                chunks.append(section)
            elif heading:
                body = "\n".join(lines[1:]).strip()
                limit = max(1, self.chunk_size - len(heading) - 1)
                chunks.extend(f"{heading}\n{part}" for part in RecursiveChunker(chunk_size=limit).chunk(body))
            else:
                chunks.extend(RecursiveChunker(chunk_size=self.chunk_size).chunk(section))
        return chunks


def _extractive_llm(prompt: str) -> str:
    return prompt.partition("Context:\n")[2].partition("\nQuestion:")[0]


def _evidence_rank(results: list[dict], evidence: str) -> int | None:
    return next((rank for rank, result in enumerate(results, 1) if evidence in result["content"].lower()), None)


def run_benchmark(strategy_name: str, chunker, root: Path) -> int:
    embedding_fn = lru_cache(maxsize=None)(_mock_embed)
    store = build_knowledge_base(root / "data/k4_ecommerce", embedding_fn, chunker=chunker)
    total = 0
    print(f"Strategy: {strategy_name} {chunker.__dict__}")
    print("Embedding backend: mock embeddings fallback")
    print(f"Chunks: {store.get_collection_size()}")
    for number, (kind, query, gold, doc_id, evidence, metadata_filter) in enumerate(QUERIES, 1):
        results = store.search_with_filter(query, top_k=3, metadata_filter=metadata_filter)
        rank = _evidence_rank(results, evidence)
        result_store = SimpleNamespace(
            search=lambda _question, top_k=3, found=results: found[:top_k],
            get_collection_size=lambda found=results: len(found),
        )
        answer = KnowledgeBaseAgent(result_store, _extractive_llm).answer(query, top_k=3)
        score = 2 if rank == 1 and evidence in answer.lower() else 1 if rank else 0
        total += score
        print(f"\nQ{number} [{kind}] filter={metadata_filter} evidence_rank={rank} score={score}/2")
        print(f"query: {query}\ngold: {gold} ({doc_id})")
        for place, result in enumerate(results, 1):
            meta = result["metadata"]
            preview = " ".join(result["content"].split())[:140]
            print(f"  {place}. {result['score']:.4f} {meta['doc_id']}::chunk_{meta['chunk_index']} | {preview}")
        print(f"agent: {' '.join(answer.split())[:220]}")
        unfiltered = store.search(query, top_k=3)
        filtered_ids = [(item["metadata"]["doc_id"], item["metadata"]["chunk_index"]) for item in results]
        unfiltered_ids = [(item["metadata"]["doc_id"], item["metadata"]["chunk_index"]) for item in unfiltered]
        print(f"A/B filter: {'changed' if filtered_ids != unfiltered_ids else 'same'} | unfiltered_evidence_rank={_evidence_rank(unfiltered, evidence)}")
    print(f"\nTOTAL: {total}/10")
    print("NOTE: mock validates flow, coherence and provenance; it does not measure semantic quality.")
    return 0
