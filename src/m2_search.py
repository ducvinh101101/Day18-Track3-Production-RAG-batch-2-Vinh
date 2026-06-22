from __future__ import annotations

"""Module 2: Hybrid Search — BM25 (Vietnamese) + Dense + RRF."""

import os, sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME, EMBEDDING_MODEL,
                    EMBEDDING_DIM, BM25_TOP_K, DENSE_TOP_K, HYBRID_TOP_K)


@dataclass
class SearchResult:
    text: str
    score: float
    metadata: dict
    method: str  # "bm25", "dense", "hybrid"


def segment_vietnamese(text: str) -> str:
    """Segment Vietnamese text into words."""
    # Vietnamese word segmentation implementation:
    # 1. from underthesea import word_tokenize
    # 2. segmented = word_tokenize(text, format="text")
    # 3. return segmented.replace("_", " ")
    #
    # ⚠️ LƯU Ý: underthesea nối từ ghép bằng "_" (VD: "nghỉ_phép").
    # BM25 tokenize bằng split(" ") → "nghỉ_phép" thành 1 token,
    # nhưng query "nghỉ phép" thành 2 token → KHÔNG khớp.
    # Phải replace("_", " ") để BM25 hoạt động đúng.
    from underthesea import word_tokenize
    segmented = word_tokenize(text, format="text")
    text = segmented.replace("_", " ")
    return text  # fallback


class BM25Search:
    def __init__(self):
        self.corpus_tokens = []
        self.documents = []
        self.bm25 = None

    def index(self, chunks: list[dict]) -> None:
        """Build BM25 index from chunks."""
        # BM25 indexing implementation:
        # 1. self.documents = chunks
        # 2. For each chunk: segment_vietnamese(chunk["text"]) → split by space
        # 3. self.corpus_tokens = [tokenized list for each chunk]
        # 4. from rank_bm25 import BM25Okapi
        #    self.bm25 = BM25Okapi(self.corpus_tokens)
        self.documents = chunks
        self.corpus_tokens = [segment_vietnamese(c["text"]).lower().split() for c in chunks]
        from rank_bm25 import BM25Okapi
        self.bm25 = BM25Okapi(self.corpus_tokens)
    
    def search(self, query: str, top_k: int = BM25_TOP_K) -> list[SearchResult]:
        """Search using BM25."""
        # BM25 search implementation:
        # 1. if self.bm25 is None: return []
        # 2. tokenized_query = segment_vietnamese(query).split()
        # 3. scores = self.bm25.get_scores(tokenized_query)
        # 4. top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        # 5. Return [SearchResult(text=..., score=..., metadata=..., method="bm25")]
        #    Lọc scores[i] > 0 để bỏ docs không liên quan.
        if self.bm25 is None:
            return []
        tokenized_query = segment_vietnamese(query).lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        results = []
        for i in range(len(scores)):
            if scores[i] > 0:
                doc = self.documents[i]
                results.append(SearchResult(
                    text=doc["text"],
                    score=float(scores[i]),
                    metadata=doc.get("metadata", {}),
                    method="bm25"
                ))
        results = sorted(results, key=lambda x: x.score, reverse=True)[:top_k]
        return results

class DenseSearch:
    def __init__(self):
        from qdrant_client import QdrantClient
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self._encoder = None

    def _get_encoder(self):
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer
            self._encoder = SentenceTransformer(EMBEDDING_MODEL)
        return self._encoder

    def index(self, chunks: list[dict], collection: str = COLLECTION_NAME) -> None:
        """Index chunks into Qdrant."""
        # Dense indexing implementation:
        # 1. from qdrant_client.models import Distance, VectorParams, PointStruct
        # 2. self.client.recreate_collection(collection, vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE))
        # 3. texts = [c["text"] for c in chunks]
        # 4. vectors = self._get_encoder().encode(texts, show_progress_bar=True)
        # 5. points = [PointStruct(id=i, vector=v.tolist(), payload={**c.get("metadata", {}), "text": c["text"]}) ...]
        # 6. self.client.upsert(collection, points)
        from qdrant_client.models import Distance, VectorParams, PointStruct
        self.client.recreate_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )
        texts = [c["text"] for c in chunks]
        vectors = self._get_encoder().encode(texts, show_progress_bar=True)
        points = [
            PointStruct(
                id=i,
                vector=v.tolist(),
                payload={**c.get("metadata", {}), "text": c["text"]}
            )
            for i, (c, v) in enumerate(zip(chunks, vectors))
        ]
        self.client.upsert(collection_name=collection, points=points)

    def search(self, query: str, top_k: int = DENSE_TOP_K, collection: str = COLLECTION_NAME) -> list[SearchResult]:
        """Search using dense vectors."""
        # Dense search implementation:
        # 1. query_vector = self._get_encoder().encode(query).tolist()
        # 2. response = self.client.query_points(collection, query=query_vector, limit=top_k)
        # 3. Return [SearchResult(text=pt.payload["text"], score=pt.score, metadata=pt.payload, method="dense")
        #            for pt in response.points]
        #
        # ⚠️ LƯU Ý: qdrant-client >= 2.0 dùng query_points(), KHÔNG phải search().
        query_vector = self._get_encoder().encode(query).tolist()
        response = self.client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=top_k
        )
        return [
            SearchResult(
                text=pt.payload["text"],
                score=float(pt.score),
                metadata={k: v for k, v in pt.payload.items() if k != "text"},
                method="dense"
            )
            for pt in response.points
        ]


def reciprocal_rank_fusion(results_list: list[list[SearchResult]], k: int = 60,
                           top_k: int = HYBRID_TOP_K) -> list[SearchResult]:
    """Merge ranked lists using RRF: score(d) = Σ 1/(k + rank)."""
    # RRF implementation:
    # 1. rrf_scores = {}  # text → {"score": float, "result": SearchResult}
    # 2. For each result_list in results_list:
    #      For rank, result in enumerate(result_list):
    #        if result.text not in rrf_scores: rrf_scores[result.text] = {"score": 0.0, "result": result}
    #        rrf_scores[result.text]["score"] += 1.0 / (k + rank + 1)
    # 3. Sort by score descending
    # 4. Return top_k SearchResult with method="hybrid"
    rrf_scores = {}
    for result_list in results_list:
        for rank, result in enumerate(result_list):
            if result.text not in rrf_scores:
                rrf_scores[result.text] = {"score": 0.0, "result": result}
            rrf_scores[result.text]["score"] += 1.0 / (k + rank + 1)
            
    sorted_items = sorted(rrf_scores.items(), key=lambda item: item[1]["score"], reverse=True)[:top_k]
    
    return [
        SearchResult(
            text=item[1]["result"].text,
            score=float(item[1]["score"]),
            metadata=item[1]["result"].metadata,
            method="hybrid"
        )
        for item in sorted_items
    ]


class HybridSearch:
    """Combines BM25 + Dense + RRF. (Đã implement sẵn — dùng classes ở trên)"""
    def __init__(self):
        self.bm25 = BM25Search()
        self.dense = DenseSearch()

    def index(self, chunks: list[dict]) -> None:
        self.bm25.index(chunks)
        self.dense.index(chunks)

    def search(self, query: str, top_k: int = HYBRID_TOP_K) -> list[SearchResult]:
        bm25_results = self.bm25.search(query, top_k=BM25_TOP_K)
        dense_results = self.dense.search(query, top_k=DENSE_TOP_K)
        return reciprocal_rank_fusion([bm25_results, dense_results], top_k=top_k)


if __name__ == "__main__":
    print(f"Original:  Nhân viên được nghỉ phép năm")
    print(f"Segmented: {segment_vietnamese('Nhân viên được nghỉ phép năm')}")
