# Evaluation results (2026-10-06)

43 labelled questions on the indexed repo, k=5, rerank pool=30. Latency is retrieval only (no LLM), on a laptop CPU.

| Mode | Recall@1 | Recall@5 | MRR | Precision@5 | p50 latency | p95 latency |
|---|---|---|---|---|---|---|
| vector | 67% | 86% | 0.75 | 32% | 22 ms | 28 ms |
| bm25 | 37% | 77% | 0.53 | 24% | 1 ms | 3 ms |
| hybrid | 60% | 84% | 0.70 | 33% | 19 ms | 28 ms |
| rerank | 60% | 84% | 0.70 | 31% | 1805 ms | 2641 ms |

**Answers** (10 questions): citation accuracy 80% (cited a correct source, no invalid citations); refused 100% of 4 out-of-scope questions.
