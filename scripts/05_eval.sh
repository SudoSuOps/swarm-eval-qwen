#!/usr/bin/env bash
set -euo pipefail

# Run all three eval suites against a model phase.
# Usage: bash scripts/05_eval.sh swarmjudge-9b-cre-b0 phase2
#        bash scripts/05_eval.sh swarmjudge-9b-cre-b0 phase2 --baseline
#        bash scripts/05_eval.sh swarmjudge-9b-cre-b0 phase2 --dry-run

MODEL="${1:?Usage: $0 MODEL PHASE [--baseline] [--dry-run]}"
PHASE="${2:?Usage: $0 MODEL PHASE [--baseline] [--dry-run]}"
EXTRA_ARGS="${3:-}"

MODEL_CONFIG="configs/models/${MODEL}/${PHASE}.yaml"
SAMPLING_CONFIG="configs/models/${MODEL}/sampling.yaml"

if [ ! -f "$MODEL_CONFIG" ]; then
    echo "ERROR: Model config not found: $MODEL_CONFIG"
    exit 1
fi

if [ ! -f "$SAMPLING_CONFIG" ]; then
    echo "ERROR: Sampling config not found: $SAMPLING_CONFIG"
    exit 1
fi

echo "=================================================="
echo "Eval — ${MODEL} ${PHASE} ${EXTRA_ARGS}"
echo "=================================================="

SUITES=(
    "configs/eval/suites/cre_core.yaml"
    "configs/eval/suites/cre_edges.yaml"
    "configs/eval/suites/cre_adversarial.yaml"
)

FAILED=0
for SUITE in "${SUITES[@]}"; do
    SUITE_NAME=$(basename "$SUITE" .yaml)
    echo ""
    echo "--- Suite: ${SUITE_NAME} ---"

    python3 -m swarmeval.eval.run_eval \
        --config "$SUITE" \
        --model-config "$MODEL_CONFIG" \
        --sampling-config "$SAMPLING_CONFIG" \
        $EXTRA_ARGS || FAILED=$((FAILED + 1))
done

echo ""
echo "=================================================="
if [ $FAILED -eq 0 ]; then
    echo "All suites completed."
else
    echo "WARNING: $FAILED suite(s) had errors."
fi
echo "=================================================="
