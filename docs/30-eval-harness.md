# Eval Harness

## Three Suites, Every Time

| Suite | File | Purpose | Size |
|-------|------|---------|------|
| `cre_core` | `evalsets/cre/core.jsonl` | Deterministic baseline | 100 cases |
| `cre_edges` | `evalsets/cre/edges.jsonl` | Borderline decisions | 50 cases |
| `cre_adversarial` | `evalsets/cre/adversarial.jsonl` | Break tests | 20 cases |

All three run on every phase eval. No exceptions.

## Metrics Tracked

| Metric | Description | Acceptance (Phase 2) |
|--------|-------------|---------------------|
| json_valid_pct | Parseable JSON output | >= 95% |
| pass_precision | When pred PASS, gold is PASS | >= 90% |
| fail_precision | When pred FAIL, gold is FAIL | >= 85% |
| pass_recall | Of gold PASS, how many caught | >= 90% |
| fail_recall | Of gold FAIL, how many caught | >= 80% |
| under_reject_rate | Gold FAIL -> pred PASS (letting bad through) | <= 10% |
| over_reject_rate | Gold PASS -> pred FAIL (too strict) | <= 15% |
| score_mae | Mean absolute error on 5-criterion scores | <= 0.5 |

## Confusion Matrix

```
             Predicted
             PASS    FAIL
Gold PASS  [ TP_P    FP_F ]   <- over-reject = FP_F / gold_PASS
Gold FAIL  [ FP_P    TP_F ]   <- under-reject = FP_P / gold_FAIL
```

Under-reject is worse than over-reject. Letting bad through is a quality failure.

## Sampling Parameters

Model inference MUST use correct parameters per Qwen family.
See `configs/models/{model_id}/sampling.yaml`.

Never use greedy decoding (`do_sample=False`) on Qwen3 or Qwen3.5.

## Regression Report

Phase N eval is always compared against Phase N-1:

- Delta on every metric (improvement or regression)
- New failures not present in Phase N-1
- Resolved failures from Phase N-1
- Per-category failure counts

Regression gate is automated in `scripts/06_regression_gate.sh`.

## Output Structure

```
results/{model_id}/{phase}/eval/
    metrics.json          Full metrics report
    failures.jsonl        All mismatches (verdict or JSON)
    confusion.csv         Confusion matrix
    samples.jsonl         First 20 outputs for inspection

results/{model_id}/{phase}/regression/
    delta_report.json     Phase N vs Phase N-1 deltas
    new_failures.jsonl    Failures new to this phase
    resolved.jsonl        Failures fixed in this phase
```
