from fastapi import APIRouter, HTTPException

from ..schemas import QueryRequest
from ..services.query_service import query_service

router = APIRouter()


@router.post('/query')
def query_documents(request: QueryRequest):
    try:
        return query_service.search(request.query, request.top_k)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Query engine failed: {exc}') from exc
