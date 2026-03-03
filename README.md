# swarm-eval-qwen

Reproducible eval, provenance, and regression gating for SwarmJudge Qwen models.

If it's not reproducible, it's not signal.

## What This Answers

| Question | Location |
|----------|----------|
| What data built this model? | `datasets/manifests/` |
| What config cooked it? | `configs/models/` |
| What did it score? | `results/` |
| What changed Phase N-1 to Phase N? | `results/.../regression/` |
| Can we detect drift on new data? | `scripts/06_regression_gate.sh` |

## Quick Start

```bash
# Validate dataset before training
make validate MODEL=swarmjudge-9b-cre-b0 PHASE=phase2

# Run eval suites (core + edges + adversarial)
make eval MODEL=swarmjudge-9b-cre-b0 PHASE=phase2

# Run baseline for comparison
make eval-baseline MODEL=swarmjudge-9b-cre-b0 PHASE=phase2

# Regression gate (Phase N vs Phase N-1)
make regression MODEL=swarmjudge-9b-cre-b0 PHASE=phase2

# Bundle release pack
make release-pack MODEL=swarmjudge-9b-cre-b0 PHASE=phase3
```

## Repo Structure

```
configs/models/{model_id}/     Frozen YAML per phase + sampling + tokenizer
configs/eval/suites/           Eval suite definitions + acceptance criteria
data_contract/schema/          JSON schemas for pairs and eval cases
data_contract/validators/      Validation scripts
datasets/manifests/            Dataset metadata + hashes (NO raw data)
datasets/fingerprints/         SHA256 checksum files
provenance/runs/               Provenance JSON per training run
src/swarmeval/                 Python eval engine
evalsets/cre/                  Eval fixtures (core, edges, adversarial)
scripts/                       Numbered workflow scripts (01-07)
results/                       Eval metrics + failures + regression deltas
docs/                          Process documentation
```

## Rules

- Raw data stays in NAS/R2. Repo stores manifests and fingerprints only.
- Every training run has a provenance.json. Missing fields = not a real run.
- Every phase runs three eval suites. No exceptions.
- Regression gate must pass before advancing phases.
- No greedy decoding on Qwen3 or Qwen3.5. Ever.
- No QLoRA on Qwen3.5. bf16 LoRA only.
- No GPU launches without approval.

## Current Status

| Model | Phase | Status |
|-------|-------|--------|
| swarmjudge-9b-cre-b0 | Phase 1 | DONE (identity lock) |
| swarmjudge-9b-cre-b0 | Phase 2 | TRAIN DONE, EVAL RUNNING |
| swarmjudge-9b-cre-b0 | Phase 3 | DATA READY (2,987 pairs) |
| swarmjudge-4b-cre-b0 | Phase 1 | DONE (identity lock, gate bench PENDING) |
| swarmjudge-2b-cre-b0 | Phase 1 | DONE (identity lock, gate bench 96% JSON) |
| swarmjudge-2b-cre-b0 | Phase 2 | PENDING (contrast learning) |

## Docs

- [Overview](docs/00-overview.md)
- [Block-0 Process](docs/10-block0-process.md)
- [Data Contract](docs/20-data-contract.md)
- [Eval Harness](docs/30-eval-harness.md)
- [Release Process](docs/40-release-process.md)
- [Incident Playbook](docs/50-incident-playbook.md)

## License

Apache 2.0
