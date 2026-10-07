# Evaluation results (2026-10-07)

43 labelled questions on the indexed repo, k=5, rerank pool=15. Latency is retrieval only (no LLM), on a laptop CPU.

| Mode | Recall@1 | Recall@5 | MRR | Precision@5 | p50 latency | p95 latency |
|---|---|---|---|---|---|---|
| vector | 79% | 93% | 0.85 | 36% | 29 ms | 33 ms |
| bm25 | 58% | 88% | 0.70 | 30% | 1 ms | 2 ms |
| hybrid | 81% | 91% | 0.85 | 37% | 29 ms | 32 ms |
| rerank | 70% | 88% | 0.78 | 34% | 1180 ms | 1380 ms |

## Recall@5 by question type

| Type | n | vector | bm25 | hybrid | rerank |
|---|---|---|---|---|---|
| docs | 8 | 75% | 62% | 75% | 75% |
| identifier | 10 | 100% | 100% | 100% | 100% |
| natural | 25 | 96% | 92% | 92% | 88% |

## Where modes disagree or all miss

| Question | vector | bm25 | hybrid | rerank |
|---|---|---|---|---|
| How does Flask parse JSON from a request body? | NO | NO | NO | NO |
| How do before_request and after_request hooks run? | yes | NO | NO | NO |
| How does Flask abort a request with an HTTP error code? | yes | yes | yes | NO |
| How do I write tests for a Flask application? | yes | NO | yes | yes |
| How do I organize a large app with blueprints? | NO | NO | NO | NO |
| What are the configuration best practices? | NO | NO | NO | NO |

## Top-3 results on `vector` misses

- **How does Flask parse JSON from a request body?** -> docs/patterns/javascript.rst (JavaScript, ``fetch``, and JSON); src/flask/json/__init__.py (jsonify); src/flask/json/provider.py (DefaultJSONProvider)
- **How do I organize a large app with blueprints?** -> src/flask/blueprints.py (Blueprint.__init__); src/flask/sansio/blueprints.py (Blueprint.register); src/flask/sansio/blueprints.py (Blueprint.app_template_global)
- **What are the configuration best practices?** -> src/flask/config.py (Config.from_mapping); commit:9efc1ebe (add SESSION_COOKIE_PARTITIONED config); docs/lifecycle.rst (Application Structure and Lifecycle)
