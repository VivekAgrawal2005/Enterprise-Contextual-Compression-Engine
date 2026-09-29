from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..services.document_service import corpus

router = APIRouter()


@router.post('/documents/upload')
def upload_documents(
    files: Annotated[list[UploadFile], File(description='PDF, TXT, or DOCX documents')],
):
    try:
        return {'documents': corpus.add_files(files)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.get('/documents')
def list_documents():
    return {'documents': list(corpus.documents.values())}

@router.post('/documents/process')
def process_documents():
    return {'documents': corpus.process()}

@router.get('/documents/{document_id}')
def get_document(document_id: str):
    if document_id not in corpus.documents:
        raise HTTPException(status_code=404, detail='Document not found')
    return corpus.documents[document_id]

@router.get('/documents/{document_id}/facts')
def get_document_facts(document_id: str):
    if document_id not in corpus.documents:
        raise HTTPException(status_code=404, detail='Document not found')
    return {'facts': [f for f in corpus.facts if f.get('document_id') == document_id]}

@router.get('/facts/{trace_id}/source')
def get_fact_source(trace_id: str):
    source = corpus.get_source(trace_id)
    if source is None:
        raise HTTPException(status_code=404, detail='Source not found')
    return source
