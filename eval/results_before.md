# Evaluation results (2026-10-06)

43 labelled questions on the indexed repo, k=5, rerank pool=15. Latency is retrieval only (no LLM), on a laptop CPU.

| Mode | Recall@1 | Recall@5 | MRR | Precision@5 | p50 latency | p95 latency |
|---|---|---|---|---|---|---|
| vector | 70% | 91% | 0.78 | 33% | 22 ms | 29 ms |
| bm25 | 40% | 79% | 0.55 | 25% | 1 ms | 3 ms |
| hybrid | 63% | 88% | 0.72 | 33% | 22 ms | 28 ms |
| rerank | 65% | 91% | 0.75 | 33% | 900 ms | 944 ms |

## Recall@5 by question type

| Type | n | vector | bm25 | hybrid | rerank |
|---|---|---|---|---|---|
| docs | 8 | 62% | 62% | 62% | 75% |
| identifier | 10 | 100% | 90% | 100% | 100% |
| natural | 25 | 96% | 80% | 92% | 92% |

## Where modes disagree or all miss

| Question | vector | bm25 | hybrid | rerank |
|---|---|---|---|---|
| How does Flask parse JSON from a request body? | NO | NO | NO | NO |
| How do before_request and after_request hooks run? | yes | NO | NO | NO |
| How does the test client simulate requests? | yes | NO | yes | yes |
| How is the g object stored for each application context? | yes | NO | yes | yes |
| How does redirect send the user to another URL? | yes | NO | yes | yes |
| MethodView | yes | NO | yes | yes |
| How do I write tests for a Flask application? | NO | NO | NO | yes |
| How do I organize a large app with blueprints? | NO | NO | NO | NO |
| What are the configuration best practices? | NO | NO | NO | NO |

## Top-3 results on `vector` misses

- **How does Flask parse JSON from a request body?** -> tests/test_json.py (test_bad_request_debug_message); tests/test_testing.py (test_json_request_and_response); docs/patterns/javascript.rst (JavaScript, ``fetch``, and JSON)
- **How do I write tests for a Flask application?** -> tests/test_basic.py (test_json_dump_dataclass); tests/test_basic.py (test_make_response); tests/test_basic.py (test_make_response_with_response_instance)
- **How do I organize a large app with blueprints?** -> src/flask/blueprints.py (Blueprint.__init__); src/flask/sansio/blueprints.py (Blueprint.register); src/flask/sansio/blueprints.py (Blueprint.app_template_global)
- **What are the configuration best practices?** -> docs/conf.py (setup); tests/test_config.py (test_config_from_envvar); src/flask/config.py (Config.from_mapping)
