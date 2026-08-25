from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

from langchain_openai import OpenAIEmbeddings

from ..core.config import Settings
from .indexer import load_documents
from .schemas import RetrievedChunk


def _tokens(text: str) -> set[str]:
    latin = re.findall(r"[A-Za-z0-9_-]+", text.lower())
    chinese = re.findall(r"[\u4e00-\u9fff]", text)
    bigrams = ["".join(chinese[i : i + 2]) for i in range(len(chinese) - 1)]
    return set(latin + chinese + bigrams)


class KnowledgeRetriever:
    def __init__(self, settings: Settings):
        self.settings = settings

    def search(self, query: str, category: str, k: int | None = None) -> list[dict]:
        k = k or self.settings.rag_top_k
        if self.settings.retrieval_provider == "lexical":
            return self._lexical_search(query, category, k)
        return self._vector_search(query, category, k)

    def _lexical_search(self, query: str, category: str, k: int) -> list[dict]:
        docs = load_documents(Path(self.settings.knowledge_base_path))
        query_tokens = _tokens(query)
        query_latin = set(re.findall(r"[A-Za-z0-9_-]+", query.lower()))
        scored = []
        for doc in docs:
            title_tokens = _tokens(doc.metadata["title"])
            doc_tokens = _tokens(doc.page_content)
            overlap = query_tokens & doc_tokens
            title_overlap = query_tokens & title_tokens
            exact_terms = sum(
                1 for term in query_latin if term and term in doc.page_content.lower()
            )
            category_bonus = 0.45 if doc.metadata["category"] in {category, "escalation"} else 0
            query_coverage = len(overlap) / max(len(query_tokens), 1)
            title_coverage = len(title_overlap) / max(len(query_tokens), 1)
            length_normalizer = 1 / math.sqrt(max(len(doc_tokens), 1))
            score = (
                query_coverage
                + title_coverage * 1.8
                + exact_terms * 0.12
                + category_bonus
                + len(overlap) * length_normalizer * 0.08
            )
            scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        selected = []
        seen_chunks: Counter[str] = Counter()
        for score, doc in scored:
            # Prefer evidence diversity when several chunks from the same document tie.
            doc_id = doc.metadata["doc_id"]
            diversity_penalty = seen_chunks[doc_id] * 0.04
            selected.append((max(score - diversity_penalty, 0.0), doc))
            seen_chunks[doc_id] += 1
        selected.sort(key=lambda item: item[0], reverse=True)
        return [self._format(doc, min(score, 1.0)) for score, doc in selected[:k]]

    def _vector_search(self, query: str, category: str, k: int) -> list[dict]:
        from langchain_chroma import Chroma

        embeddings = OpenAIEmbeddings(
            model=self.settings.embedding_model,
            api_key=self.settings.effective_embedding_api_key,
            base_url=self.settings.effective_embedding_base_url,
        )
        store = Chroma(
            collection_name="expense_support_kb",
            embedding_function=embeddings,
            persist_directory=str(self.settings.chroma_path),
        )
        results = store.similarity_search_with_relevance_scores(
            query, k=k, filter={"category": category}
        )
        if len(results) < k:
            results = store.similarity_search_with_relevance_scores(query, k=k)
        return [self._format(doc, max(0.0, min(float(score), 1.0))) for doc, score in results[:k]]

    @staticmethod
    def _format(doc, score: float) -> dict:
        return RetrievedChunk(
            content=doc.page_content,
            score=score,
            **doc.metadata,
        ).model_dump()
