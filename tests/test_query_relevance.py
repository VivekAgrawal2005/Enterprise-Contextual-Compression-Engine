import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from query_engine import QueryEngine


QUERY_SETS = {
    'in_domain': [
        'What is the daily withdrawal limit?',
        'How many ATM transactions are allowed per day?',
        'What is the deadline for completing an investigation?',
        'Who approves emergency maintenance exceeding two hours?',
        'How long must the investigation be completed within?',
    ],
    'out_of_domain': [
        'What is the weather in Pune today?',
        'Who won the latest cricket match?',
        'What is the capital of France?',
        'Write a Python program to reverse a string.',
        "What is today's stock price?",
    ],
}


def build_engine():
    return QueryEngine(compressed_data_path='compressed_output.json', top_k=5)


def test_in_domain_queries_return_relevant_results():
    engine = build_engine()
    for query in QUERY_SETS['in_domain']:
        results = engine.query(query, top_k=5)
        assert results, f'Expected relevant results for: {query}'
        best_similarity = engine.get_last_debug_info().get('best_similarity', 0.0)
        assert best_similarity >= engine.relevance_threshold, (
            f'Query was rejected despite being in-domain: {query} (score={best_similarity})'
        )


def test_out_of_domain_queries_are_rejected():
    engine = build_engine()
    for query in QUERY_SETS['out_of_domain']:
        results = engine.query(query, top_k=5)
        debug = engine.get_last_debug_info()
        assert not results, f'Out-of-domain query incorrectly returned results: {query}'
        assert debug.get('status') == 'OUT_OF_DOMAIN', (
            f'Expected OUT_OF_DOMAIN status for: {query}, got {debug.get("status")}'
        )


def test_returned_response_is_clear_and_specific():
    engine = build_engine()
    query = 'What is the weather in Pune today?'
    results = engine.query(query, top_k=5)
    assert not results
    debug = engine.get_last_debug_info()
    assert debug.get('status') == 'OUT_OF_DOMAIN'
    assert debug.get('best_similarity', 0.0) < engine.relevance_threshold


def test_evaluation_report_runs():
    engine = build_engine()
    report = engine.evaluate_queries(QUERY_SETS)
    assert report['total_in_domain'] == len(QUERY_SETS['in_domain'])
    assert report['total_out_of_domain'] == len(QUERY_SETS['out_of_domain'])
    assert report['false_positive_retrievals'] == 0
    assert report['correct_in_domain'] == len(QUERY_SETS['in_domain'])
    assert report['correct_out_of_domain'] == len(QUERY_SETS['out_of_domain'])
