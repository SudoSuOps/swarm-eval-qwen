#!/usr/bin/env bash
set -euo pipefail

# Run regression gate — compare Phase N vs Phase N-1.
# Usage: bash scripts/06_regression_gate.sh swarmjudge-9b-cre-b0 phase2

MODEL="${1:?Usage: $0 MODEL PHASE}"
PHASE="${2:?Usage: $0 MODEL PHASE}"

# Determine previous phase
case "$PHASE" in
    phase2) PREV="phase1" ;;
    phase3) PREV="phase2" ;;
    *) echo "ERROR: Unknown phase $PHASE"; exit 1 ;;
esac

CURRENT="results/${MODEL}/${PHASE}/eval/metrics.json"
BASELINE="results/${MODEL}/${PREV}/eval/metrics.json"
OUTPUT="results/${MODEL}/${PHASE}/regression/delta_report.json"

if [ ! -f "$CURRENT" ]; then
    echo "ERROR: Current metrics not found: $CURRENT"
    echo "Run eval first: make eval MODEL=$MODEL PHASE=$PHASE"
    exit 1
fi

if [ ! -f "$BASELINE" ]; then
    echo "ERROR: Baseline metrics not found: $BASELINE"
    echo "Run baseline eval first: make eval-baseline MODEL=$MODEL PHASE=$PREV"
    exit 1
fi

python3 -m swarmeval.eval.regression \
    --current "$CURRENT" \
    --baseline "$BASELINE" \
    --threshold 2.0 \
    --output "$OUTPUT"
