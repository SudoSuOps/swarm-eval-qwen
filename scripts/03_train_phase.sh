#!/usr/bin/env bash
set -euo pipefail

# Train a phase. Reads frozen config, validates data first, then launches.
# Usage: bash scripts/03_train_phase.sh swarmjudge-9b-cre-b0 phase2

MODEL="${1:?Usage: $0 MODEL PHASE}"
PHASE="${2:?Usage: $0 MODEL PHASE}"

CONFIG="configs/models/${MODEL}/${PHASE}.yaml"

if [ ! -f "$CONFIG" ]; then
    echo "ERROR: Config not found: $CONFIG"
    exit 1
fi

echo "=================================================="
echo "Training — ${MODEL} ${PHASE}"
echo "=================================================="
echo "Config: $CONFIG"
echo ""

# Step 1: Validate data
echo "Step 1: Validate data..."
bash scripts/02_validate_data.sh "$MODEL" "$PHASE"

# Step 2: Hash config
CONFIG_SHA=$(sha256sum "$CONFIG" | awk '{print $1}')
echo ""
echo "Config SHA256: $CONFIG_SHA"

# Step 3: Record git commit
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo "Git commit: $GIT_SHA"

echo ""
echo "Data validated. Config hashed. Ready to train."
echo ""
echo "Launch training manually on swarmrails with:"
echo "  ssh swarmrails \"CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 \\"
echo "    nohup python3 /path/to/train_script.py \\"
echo "    > /data2/${MODEL//-/_}/${PHASE}/train.log 2>&1 &\""
echo ""
echo "This script does NOT launch GPU work automatically."
echo "Review config, confirm GPU allocation, then launch."
