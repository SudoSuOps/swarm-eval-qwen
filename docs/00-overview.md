# Overview

swarm-eval-qwen is the reproducibility and provenance backbone for SwarmJudge model builds.

If it's not reproducible, it's not signal.

## What this repo answers

| Question | Where |
|----------|-------|
| What data built this model? | `datasets/manifests/` — hashes + counts + splits |
| What config cooked it? | `configs/models/` — frozen YAML per phase |
| What did it score? | `results/` — eval metrics + failures + confusion |
| What changed Phase N-1 → Phase N? | `results/.../regression/` — deltas + targeted failures |
| Can we detect drift? | `scripts/06_regression_gate.sh` — automated pass/fail |

## What this repo does NOT contain

- Raw training data (stays in NAS/R2)
- Model weights (stays in NAS/R2)
- API keys or secrets

## Naming Convention

| Entity | Format | Example |
|--------|--------|---------|
| Model ID | `{name}-{params}-{domain}-{block}` | `swarmjudge-9b-cre-b0` |
| Phase | `phase1` / `phase2` / `phase3` | `phase2` |
| Release | `v{major}.{minor}.{patch}` | `v1.0.0` |
| Run ID | `{YYYYMMDD}-{HHMM}-{shortsha}` | `20260303-1914-a3b2c1d` |

## Model Families

This repo tracks models built on two Qwen families. They are NOT interchangeable.

| Family | Architecture | Think Default (<=9B) | Context |
|--------|-------------|---------------------|---------|
| Qwen3 | Standard Transformer + GQA | ON | 32K / 131K YaRN |
| Qwen3.5 | GDN + sparse MoE | OFF | 262K / 1M YaRN |

See `configs/models/*/sampling.yaml` for correct inference parameters per family.
