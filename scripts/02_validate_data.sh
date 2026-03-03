#!/usr/bin/env bash
set -euo pipefail

# Validate dataset before training.
# Usage: bash scripts/02_validate_data.sh swarmjudge-9b-cre-b0 phase2

MODEL="${1:?Usage: $0 MODEL PHASE}"
PHASE="${2:?Usage: $0 MODEL PHASE}"

MANIFEST="datasets/manifests/${MODEL}/${PHASE}.manifest.json"

if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: Manifest not found: $MANIFEST"
    exit 1
fi

echo "=================================================="
echo "Data Validation — ${MODEL} ${PHASE}"
echo "=================================================="

# Extract paths from manifest
TRAIN_PATH=$(python3 -c "import json; m=json.load(open('$MANIFEST')); print(m['dataset_location']['train'])")
EVAL_PATH=$(python3 -c "import json; m=json.load(open('$MANIFEST')); print(m['dataset_location'].get('eval',''))")
EXPECTED_PASS=$(python3 -c "import json; m=json.load(open('$MANIFEST')); t=m['pass_count']+m['fail_count']; print(round(100*m['pass_count']/t,1) if t else '')" 2>/dev/null || echo "")

echo "  Manifest: $MANIFEST"
echo "  Train:    $TRAIN_PATH"
echo "  Eval:     $EVAL_PATH"

# Check if files are local or R2
if [[ "$TRAIN_PATH" == r2://* ]]; then
    echo "  NOTE: Dataset is in R2. Pull locally before validation."
    echo "  Run: npx wrangler r2 object get ..."
    exit 1
fi

if [ ! -f "$TRAIN_PATH" ]; then
    echo "ERROR: Train file not found: $TRAIN_PATH"
    exit 1
fi

# Run pair validator
ARGS="--train $TRAIN_PATH"
if [ -n "$EVAL_PATH" ] && [ -f "$EVAL_PATH" ]; then
    ARGS="$ARGS --eval $EVAL_PATH"
fi
if [ -n "$EXPECTED_PASS" ]; then
    ARGS="$ARGS --expected-pass-pct $EXPECTED_PASS"
fi

python3 data_contract/validators/validate_pairs.py $ARGS

echo ""
echo "Validation complete."
