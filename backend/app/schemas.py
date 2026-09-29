from typing import Any, Optional
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)

class QueryResponse(BaseModel):
    status: str
    best_similarity: float = 0.0
    threshold: float = 0.35
    results: list[dict[str, Any]] = []

class DocumentSummary(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    facts_extracted: int = 0
    retained_facts: int = 0
    compression_stats: dict[str, Any] = {}
    error: Optional[str] = None
