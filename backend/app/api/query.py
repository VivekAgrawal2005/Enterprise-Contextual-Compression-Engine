from fastapi import APIRouter
from ..schemas import QueryRequest
from ..services.document_service import corpus

router = APIRouter()

@router.post('/query')
def query_documents(request: QueryRequest):
    if not corpus.query_engine or not corpus.facts:
        return {'status': 'EMPTY_CORPUS', 'best_similarity': 0.0, 'threshold': 0.35, 'results': []}
    try:
        results = corpus.query_engine.query(request.query, request.top_k)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Query engine failed: {exc}') from exc
    best = results[0]['similarity_score'] if results else 0.0
    if best < 0.35:
        return {'status': 'OUT_OF_DOMAIN', 'best_similarity': best, 'threshold': 0.35, 'results': []}
    return {'status': 'OK', 'best_similarity': best, 'threshold': 0.35, 'results': results}

@router.get('/facts/{trace_id}/source')
def source(trace_id: str):
    return corpus.get_source(trace_id) or {'paragraph_text': '', 'section_title': 'Unknown'}
