import hashlib
import json
import shutil
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
UPLOADS = ROOT / 'runtime' / 'uploads'
ARTIFACTS = ROOT / 'runtime' / 'artifacts'
UPLOADS.mkdir(parents=True, exist_ok=True)
ARTIFACTS.mkdir(parents=True, exist_ok=True)

class CorpusService:
    @staticmethod
    def trace_id_for_fact(fact: dict[str, Any]) -> str:
        existing = fact.get('trace_id') or fact.get('source', {}).get('trace_id')
        if existing:
            return str(existing)

        source = fact.get('source') or {}
        document_id = fact.get('document_id') or source.get('document_id') or 'unknown'
        section_id = fact.get('section_id') or source.get('section_id') or 'unknown'
        paragraph_id = fact.get('paragraph_id') or source.get('paragraph_id') or 'unknown'
        identity = '\x1f'.join((str(document_id), str(section_id), str(paragraph_id)))
        return hashlib.sha256(identity.encode('utf-8')).hexdigest()

    def __init__(self):
        self.documents: dict[str, dict[str, Any]] = {}
        self.facts: list[dict[str, Any]] = []
        self.structures: dict[str, Any] = {}
        self.query_engine = None

    def add_files(self, files):
        added = []
        for upload in files:
            suffix = Path(upload.filename or '').suffix.lower()
            if suffix not in {'.pdf', '.txt', '.docx'}:
                raise ValueError(f'Unsupported file type: {suffix or "unknown"}')
            document_id = uuid.uuid4().hex
            target = UPLOADS / f'{document_id}{suffix}'
            with target.open('wb') as output:
                shutil.copyfileobj(upload.file, output)
            item = {'document_id': document_id, 'filename': upload.filename, 'file_type': suffix[1:].upper(), 'file_size': target.stat().st_size, 'status': 'Queued', 'path': str(target), 'facts_extracted': 0, 'retained_facts': 0, 'compression_stats': {}}
            self.documents[document_id] = item
            added.append(item)
        return added

    def process(self):
        from src.main import ContextualCompressionEngine
        engine = ContextualCompressionEngine(importance_threshold=0.5, min_confidence=0.4)
        all_facts = []
        for doc in self.documents.values():
            if doc['status'] == 'Completed':
                continue
            doc['status'] = 'Processing'
            try:
                result = engine.process_document(doc['path'])
                facts = result.get('compressed_facts', [])
                all_facts.extend(facts)
                doc['status'] = 'Completed'
                stats = result.get('metadata', {}).get('compression_stats', result.get('compression_stats', {}))
                doc['facts_extracted'] = stats.get('total_facts', len(facts))
                doc['retained_facts'] = stats.get('selected_facts', len(facts))
                doc['compression_stats'] = stats
                self.structures[doc['document_id']] = engine.drilldown
            except Exception as exc:
                doc['status'] = 'Failed'
                doc['error'] = str(exc)
        self.facts = all_facts
        if self.facts:
            from src.query_engine import QueryEngine
            self.query_engine = QueryEngine(compressed_data={'compressed_facts': self.facts, 'metadata': {'total_documents': len(self.documents)}})
            self.query_engine.set_drilldown_manager(next(iter(self.structures.values()), None))
        return list(self.documents.values())

    def get_source(self, trace_id: str):
        for fact in self.facts:
            if self.trace_id_for_fact(fact) == trace_id:
                if self.query_engine:
                    return self.query_engine.get_source_text(fact) or {
                        'document_id': fact.get('document_id'),
                        'paragraph_text': '',
                        'section_title': fact.get('section_id', 'Unknown'),
                    }
        return None

corpus = CorpusService()
