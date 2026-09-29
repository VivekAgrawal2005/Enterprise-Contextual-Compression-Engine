from fastapi import APIRouter
from ..services.document_service import corpus
router = APIRouter()
@router.get('/health')
def health():
    return {'status': 'healthy', 'documents': len(corpus.documents), 'facts': len(corpus.facts)}
