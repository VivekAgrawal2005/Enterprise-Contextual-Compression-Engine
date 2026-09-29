# Query Relevance Evaluation Report

## Scope

This report validates the retrieval safety fix for the document-intelligence prototype. The system is designed to answer questions only from the indexed document corpus and reject unsupported prompts before returning facts.

## Validation commands

```bash
cd "C:\Users\vivek\OneDrive\Desktop\cursor projects\PS4"
& "C:\DL CP\myenv\Scripts\python.exe" -m pytest -q
& "C:\DL CP\myenv\Scripts\python.exe" eval_query_relevance.py
& "C:\DL CP\myenv\Scripts\python.exe" -c "from src.query_engine import QueryEngine; engine=QueryEngine(compressed_data_path='compressed_output.json', top_k=5); resp=engine.query('What is the weather in Pune today?'); print({'status': engine.get_last_debug_info().get('status'), 'best_similarity': engine.get_last_debug_info().get('best_similarity'), 'relevance_threshold': engine.relevance_threshold, 'result_count': len(resp)})"
```

## Results

### Test suite

- `pytest -q` result: 4 passed in 37.16s

### Query evaluation summary

- Total in-domain queries: 4
- Correctly answered: 4
- Total out-of-domain queries: 5
- Correctly rejected: 5
- False positive retrievals: 0

### Observed similarity scores

| Query type    | Example query                                           |  Score |
| ------------- | ------------------------------------------------------- | -----: |
| In-domain     | What is the daily withdrawal limit?                     | 0.8260 |
| In-domain     | How many ATM transactions are allowed per day?          | 0.9019 |
| In-domain     | What is the deadline for completing an investigation?   | 0.7194 |
| In-domain     | Who approves emergency maintenance exceeding two hours? | 0.8411 |
| Out-of-domain | What is the weather in Pune today?                      | 0.2040 |
| Out-of-domain | Who won the latest cricket match?                       | 0.1125 |
| Out-of-domain | What is the capital of France?                          | 0.0475 |
| Out-of-domain | Write a Python program to reverse a string.             | 0.0947 |
| Out-of-domain | What is today's stock price?                            | 0.2862 |

### Threshold

- Relevance threshold: 0.35

### Exact unsupported-query check

Query: "What is the weather in Pune today?"

- Status: OUT_OF_DOMAIN
- Best similarity: 0.2040
- Relevance threshold: 0.35
- Result count: 0

## Interpretation

The observed scores show a clear separation between in-domain and unsupported queries. The threshold-based relevance gate is effective and does not overfit to a single topic such as weather; it protects the system from unrelated prompts while preserving valid domain retrievals.
