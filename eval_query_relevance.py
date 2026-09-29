import json
from pathlib import Path
from src.query_engine import QueryEngine


IN_DOMAIN = [
    'What is the daily withdrawal limit?',
    'How many ATM transactions are allowed per day?',
    'What is the deadline for completing an investigation?',
    'Who approves emergency maintenance exceeding two hours?',
]

OUT_OF_DOMAIN = [
    'What is the weather in Pune today?',
    'Who won the latest cricket match?',
    'What is the capital of France?',
    'Write a Python program to reverse a string.',
    "What is today's stock price?",
]


def run_evaluation():
    engine = QueryEngine(compressed_data_path='compressed_output.json', top_k=5)
    report = engine.evaluate_queries({'in_domain': IN_DOMAIN, 'out_of_domain': OUT_OF_DOMAIN})

    print('=== Query Relevance Evaluation ===')
    print(f"Total in-domain queries: {report['total_in_domain']}")
    print(f"Correctly answered: {report['correct_in_domain']}")
    print(f"Total out-of-domain queries: {report['total_out_of_domain']}")
    print(f"Correctly rejected: {report['correct_out_of_domain']}")
    print(f"False positive retrievals: {report['false_positive_retrievals']}")
    print()

    for detail in report['details']:
        print(f"Query: {detail['query']}")
        print(f"  Label: {detail['label']}")
        print(f"  Best similarity score: {detail['best_similarity']:.4f}")
        print(f"  Threshold: {detail['relevance_threshold']:.4f}")
        print(f"  Status: {detail['status']}")
        print(f"  Returned results: {detail['result_count']}")
        print()

    return report


if __name__ == '__main__':
    run_evaluation()
