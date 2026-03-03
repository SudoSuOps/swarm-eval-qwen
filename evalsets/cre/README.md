# CRE Eval Sets

Three suites, every phase, no exceptions.

| Suite | File | Cases | Purpose |
|-------|------|-------|---------|
| Core | `core.jsonl` | 100 | Deterministic baseline (50 PASS + 50 FAIL) |
| Edges | `edges.jsonl` | 50 | Borderline decisions |
| Adversarial | `adversarial.jsonl` | 20 | Break tests |

## Schema

Every case validates against `data_contract/schema/evalcase.schema.json`.

## Building Eval Sets

Core and edges are sampled from Phase 2 eval holdout.
Adversarial cases are hand-crafted from known failure categories.

Phase 3 adds specialty-specific cases to all three suites.
