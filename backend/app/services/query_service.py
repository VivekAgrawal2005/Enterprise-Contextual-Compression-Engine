from typing import Any

from .document_service import corpus


class QueryService:
    """Application service for querying the engine-backed document corpus."""

    OUT_OF_DOMAIN_THRESHOLD = 0.35

    def search(self, query: str, top_k: int = 5) -> dict[str, Any]:
        if not corpus.query_engine or not corpus.facts:
            return {
                'status': 'EMPTY_CORPUS',
                'best_similarity': 0.0,
                'threshold': self.OUT_OF_DOMAIN_THRESHOLD,
                'results': [],
            }

        results = corpus.query_engine.query(query, top_k=max(1, min(top_k, 50)))
        best_similarity = results[0]['similarity_score'] if results else 0.0
        if best_similarity < self.OUT_OF_DOMAIN_THRESHOLD:
            return {
                'status': 'OUT_OF_DOMAIN',
                'best_similarity': best_similarity,
                'threshold': self.OUT_OF_DOMAIN_THRESHOLD,
                'results': [],
            }

        return {
            'status': 'OK',
            'best_similarity': best_similarity,
            'threshold': self.OUT_OF_DOMAIN_THRESHOLD,
            'results': results,
        }


query_service = QueryService()

__all__ = ['QueryService', 'query_service']
