"""
Query Engine Module

Provides semantic search over compressed facts using sentence embeddings
and cosine similarity. Supports drill-down to original source text.
"""

import json
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_RELEVANCE_THRESHOLD = 0.35
NO_RELEVANCE_MESSAGE = (
    "No sufficiently relevant information was found in the indexed documents. "
    "This system answers questions only from the information contained in the indexed document corpus."
)


class QueryEngine:
    """
    Semantic search engine for querying compressed facts.
    """
    
    def __init__(
        self,
        compressed_data_path: Optional[str] = None,
        compressed_data: Optional[Dict[str, Any]] = None,
        model_name: str = 'all-MiniLM-L6-v2',
        top_k: int = 5,
        relevance_threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
        debug: bool = False
    ):
        """
        Initialize the query engine.

        Args:
            compressed_data_path: Path to compressed_output.json file
            compressed_data: Optional pre-loaded compressed data dictionary
            model_name: Sentence transformer model name
            top_k: Number of top results to return
            relevance_threshold: Minimum similarity score required to accept a query as in-domain
            debug: Whether to keep verbose decision metadata for each query
        """
        logger.info("Initializing Query Engine...")

        # Load compressed data
        if compressed_data is not None:
            self.compressed_data = compressed_data
        elif compressed_data_path:
            self.compressed_data = self._load_compressed_data(compressed_data_path)
        else:
            raise ValueError("Either compressed_data_path or compressed_data must be provided")

        # Extract facts
        self.facts = self.compressed_data.get('compressed_facts', [])

        if not self.facts:
            raise ValueError("No compressed facts found in data")

        logger.info(f"Loaded {len(self.facts)} compressed facts")

        # Initialize sentence transformer
        logger.info(f"Loading sentence transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)

        # Generate embeddings for all facts
        logger.info("Generating embeddings for facts...")
        self.fact_texts = [fact.get('fact_text', '') for fact in self.facts]
        self.fact_embeddings = self.model.encode(
            self.fact_texts,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        logger.info("Query engine initialized successfully")

        self.top_k = top_k
        self.relevance_threshold = relevance_threshold
        self.debug = debug
        self.drilldown_manager = None
        self.last_query_debug = {}
        self.last_query_status = 'UNKNOWN'
    
    def _load_compressed_data(self, file_path: str) -> Dict[str, Any]:
        """
        Load compressed data from JSON file.
        
        Args:
            file_path: Path to compressed_output.json
            
        Returns:
            Loaded compressed data dictionary
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded compressed data from: {file_path}")
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"Compressed data file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in compressed data file: {e}")
    
    def set_drilldown_manager(self, drilldown_manager):
        """
        Set drill-down manager for source retrieval.
        
        Args:
            drilldown_manager: DrillDownManager instance
        """
        self.drilldown_manager = drilldown_manager
        logger.info("Drill-down manager set")
    
    def query(
        self,
        query_text: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query compressed facts using semantic similarity.

        The retrieval pipeline first computes candidate matches using the existing
        similarity mechanism. It then applies a generic relevance gate: if the best
        candidate is below the configured threshold, the query is treated as
        out-of-domain and no unrelated facts are returned.

        Args:
            query_text: User query string
            top_k: Number of top results to return (overrides default)

        Returns:
            List of matching facts with similarity scores, sorted by relevance
        """
        if not query_text.strip():
            self.last_query_debug = {
                'query': query_text,
                'best_similarity': 0.0,
                'relevance_threshold': self.relevance_threshold,
                'candidate_count': 0,
                'status': 'OUT_OF_DOMAIN',
                'message': NO_RELEVANCE_MESSAGE,
            }
            self.last_query_status = 'OUT_OF_DOMAIN'
            return []

        k = top_k if top_k is not None else self.top_k

        # Generate embedding for query
        query_embedding = self.model.encode(
            [query_text],
            show_progress_bar=False,
            convert_to_numpy=True
        )

        # Compute cosine similarity
        similarities = cosine_similarity(query_embedding, self.fact_embeddings)[0]
        best_similarity = float(np.max(similarities)) if len(similarities) else 0.0
        top_indices = np.argsort(similarities)[::-1][:k]

        self.last_query_debug = {
            'query': query_text,
            'best_similarity': round(best_similarity, 4),
            'relevance_threshold': self.relevance_threshold,
            'candidate_count': len(top_indices),
            'status': 'RELEVANT' if best_similarity >= self.relevance_threshold else 'OUT_OF_DOMAIN',
            'message': NO_RELEVANCE_MESSAGE if best_similarity < self.relevance_threshold else '',
        }
        self.last_query_status = self.last_query_debug['status']

        if best_similarity < self.relevance_threshold:
            logger.info(
                "Rejecting query as out-of-domain: best_similarity=%.4f, threshold=%.4f, query='%s'",
                best_similarity,
                self.relevance_threshold,
                query_text,
            )
            return []

        # Build results for relevant queries
        results = []
        for idx in top_indices:
            fact = self.facts[idx].copy()
            similarity_score = float(similarities[idx])

            result = {
                'fact_text': fact.get('fact_text', ''),
                'importance_score': fact.get('importance_score', 0.0),
                'confidence_score': fact.get('confidence_score', 0.0),
                'combined_score': fact.get('combined_score', 0.0),
                'fact_type': fact.get('fact_type', 'unknown'),
                'similarity_score': round(similarity_score, 4),
                'document_id': fact.get('document_id', 'unknown'),
                'section_id': fact.get('section_id', 'unknown'),
                'paragraph_id': fact.get('paragraph_id', 'unknown'),
                'source': fact.get('source', {})
            }

            results.append(result)

        logger.info(
            "Query accepted: best_similarity=%.4f, threshold=%.4f, returned=%d results",
            best_similarity,
            self.relevance_threshold,
            len(results),
        )
        return results
    
    def get_source_text(
        self,
        fact: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve original source text for a fact using drill-down.
        
        Args:
            fact: Fact dictionary with source information
            
        Returns:
            Dictionary with source text information or None if not available
        """
        document_id = fact.get('document_id', 'unknown')
        section_id = fact.get('section_id', 'unknown')
        paragraph_id = fact.get('paragraph_id', 'unknown')
        
        # Try drill-down manager first
        if self.drilldown_manager:
            source_info = self.drilldown_manager.get_fact_source(fact)
            
            if source_info:
                return {
                    'paragraph_text': source_info['paragraph'].get('text', ''),
                    'section_title': source_info.get('section_title', 'Unknown Section'),
                    'document_id': document_id
                }
        
        # Fallback: Try to get from traceability manager if available
        if self.drilldown_manager and hasattr(self.drilldown_manager, 'traceability'):
            traceability = self.drilldown_manager.traceability
            original_text = traceability.get_original_paragraph(
                document_id, section_id, paragraph_id
            )
            
            if original_text:
                return {
                    'paragraph_text': original_text,
                    'section_title': 'Unknown Section',
                    'document_id': document_id
                }
        
        return None
    
    def get_last_debug_info(self) -> Dict[str, Any]:
        """Return the last query decision debug metadata."""
        return self.last_query_debug.copy()

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get document metadata from compressed data.

        Returns:
            Metadata dictionary
        """
        return self.compressed_data.get('metadata', {})

    def get_compression_stats(self) -> Dict[str, Any]:
        """
        Get compression statistics.

        Returns:
            Compression statistics dictionary
        """
        return self.compressed_data.get('compression_stats', {})

    def evaluate_queries(self, query_sets: Dict[str, List[str]]) -> Dict[str, Any]:
        """Evaluate a set of in-domain and out-of-domain queries and return summary stats."""
        report = {
            'total_in_domain': 0,
            'correct_in_domain': 0,
            'total_out_of_domain': 0,
            'correct_out_of_domain': 0,
            'false_positive_retrievals': 0,
            'details': []
        }

        for label, queries in query_sets.items():
            for query in queries:
                results = self.query(query, top_k=5)
                debug = self.get_last_debug_info()
                status = debug.get('status', 'OUT_OF_DOMAIN')
                best_similarity = debug.get('best_similarity', 0.0)
                accepted = bool(results)
                is_in_domain = label == 'in_domain'

                if is_in_domain:
                    report['total_in_domain'] += 1
                    if accepted and status == 'RELEVANT':
                        report['correct_in_domain'] += 1
                else:
                    report['total_out_of_domain'] += 1
                    if not accepted and status == 'OUT_OF_DOMAIN':
                        report['correct_out_of_domain'] += 1
                    elif accepted and status == 'RELEVANT':
                        report['false_positive_retrievals'] += 1

                report['details'].append({
                    'query': query,
                    'label': label,
                    'status': status,
                    'best_similarity': round(best_similarity, 4),
                    'accepted': accepted,
                    'relevance_threshold': self.relevance_threshold,
                    'result_count': len(results),
                })

        return report
