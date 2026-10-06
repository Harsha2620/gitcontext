# Evaluation results (2026-10-06)

43 labelled questions on the indexed repo, k=5, rerank pool=15. Latency is retrieval only (no LLM), on a laptop CPU.

| Mode | Recall@1 | Recall@5 | MRR | Precision@5 | p50 latency | p95 latency |
|---|---|---|---|---|---|---|
| vector | 67% | 86% | 0.75 | 32% | 27 ms | 29 ms |
| bm25 | 37% | 77% | 0.53 | 24% | 1 ms | 2 ms |
| hybrid | 60% | 84% | 0.69 | 32% | 29 ms | 39 ms |
| rerank | 60% | 86% | 0.70 | 32% | 1396 ms | 2258 ms |

## Recall@5 by question type

| Type | n | vector | bm25 | hybrid | rerank |
|---|---|---|---|---|---|
| docs | 8 | 50% | 50% | 50% | 62% |
| identifier | 10 | 100% | 90% | 100% | 100% |
| natural | 25 | 92% | 80% | 88% | 88% |

## Where modes disagree or all miss

| Question | vector | bm25 | hybrid | rerank |
|---|---|---|---|---|
| How does Flask parse JSON from a request body? | NO | NO | NO | NO |
| How do before_request and after_request hooks run? | yes | NO | NO | NO |
| How does the test client simulate requests? | NO | NO | NO | NO |
| How is the g object stored for each application context? | yes | NO | yes | yes |
| How does redirect send the user to another URL? | yes | NO | yes | yes |
| MethodView | yes | NO | yes | yes |
| How do I configure logging in Flask? | NO | NO | NO | NO |
| How do I write tests for a Flask application? | NO | NO | NO | yes |
| How do I organize a large app with blueprints? | NO | NO | NO | NO |
| What are the configuration best practices? | NO | NO | NO | NO |

## Top-3 results on `vector` misses

- **How does Flask parse JSON from a request body?** -> tests/test_json.py (test_bad_request_debug_message); tests/test_testing.py (test_json_request_and_response); docs/patterns/javascript.rst (JavaScript, ``fetch``, and JSON)
- **How does the test client simulate requests?** -> tests/test_basic.py (test_request_processing); docs/testing.rst (Testing Flask Applications); src/flask/app.py (Flask.test_client)
- **How do I configure logging in Flask?** -> src/flask/logging.py (create_logger); tests/test_logging.py (reset_logging); tests/test_logging.py (test_logger)
- **How do I write tests for a Flask application?** -> tests/test_basic.py (test_json_dump_dataclass); tests/test_basic.py (test_make_response); tests/test_basic.py (test_make_response_with_response_instance)
- **How do I organize a large app with blueprints?** -> src/flask/blueprints.py (Blueprint.__init__); src/flask/sansio/blueprints.py (Blueprint.register); src/flask/sansio/blueprints.py (Blueprint.app_template_global)
- **What are the configuration best practices?** -> docs/conf.py (setup); tests/test_config.py (test_config_from_envvar); src/flask/config.py (Config.from_mapping)
