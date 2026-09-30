from backend.app.api import documents as documents_api
from backend.app.services.document_service import CorpusService
from src.drilldown import DrillDownManager
from src.traceability import TraceabilityManager


def test_source_route_returns_original_paragraph_text(monkeypatch):
    corpus = CorpusService()
    fact = {
        'fact_text': 'The retention period is seven years.',
        'document_id': 'policy_document',
        'section_id': 'policy_document_section_0',
        'paragraph_id': 'policy_document_section_0_para_0',
    }
    manager = DrillDownManager(TraceabilityManager())
    manager.register_document_structure(
        'policy_document',
        {
            'document_id': 'policy_document',
            'sections': [
                {
                    'section_id': 'policy_document_section_0',
                    'title': 'Records Retention',
                    'paragraphs': [
                        {
                            'paragraph_id': 'policy_document_section_0_para_0',
                            'text': 'The original policy paragraph requires records to be retained for seven years.',
                        }
                    ],
                }
            ],
        },
    )
    corpus.facts = [fact]
    corpus.structures['policy_document'] = manager
    monkeypatch.setattr(documents_api, 'corpus', corpus)

    trace_id = corpus.trace_id_for_fact(fact)
    response = corpus.get_source(trace_id)

    assert response is not None
    assert response['trace_id'] == trace_id
    assert response['paragraph_text']
    assert 'retained for seven years' in response['paragraph_text']

    route_response = documents_api.get_fact_source(trace_id)
    assert route_response['paragraph_text'] == response['paragraph_text']
    assert route_response['text'] == response['paragraph_text']