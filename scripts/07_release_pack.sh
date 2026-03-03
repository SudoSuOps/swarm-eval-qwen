#!/usr/bin/env bash
set -euo pipefail

# Generate release pack for a sealed block.
# Usage: bash scripts/07_release_pack.sh swarmjudge-9b-cre-b0 phase3

MODEL="${1:?Usage: $0 MODEL FINAL_PHASE}"
PHASE="${2:?Usage: $0 MODEL FINAL_PHASE}"

RELEASE_DIR="release_pack/${MODEL}"
mkdir -p "$RELEASE_DIR"

echo "=================================================="
echo "Release Pack — ${MODEL}"
echo "=================================================="

# Collect eval reports
echo "Collecting eval reports..."
for P in phase1 phase2 phase3; do
    METRICS="results/${MODEL}/${P}/eval/metrics.json"
    if [ -f "$METRICS" ]; then
        cp "$METRICS" "$RELEASE_DIR/${P}_metrics.json"
        echo "  ${P}: OK"
    else
        echo "  ${P}: MISSING"
    fi
done

# Collect configs
echo "Collecting configs..."
mkdir -p "$RELEASE_DIR/configs"
cp configs/models/${MODEL}/*.yaml "$RELEASE_DIR/configs/" 2>/dev/null || echo "  No configs found"

# Collect provenance
echo "Collecting provenance..."
mkdir -p "$RELEASE_DIR/provenance"
for P in phase1 phase2 phase3; do
    PROV="provenance/runs/${MODEL}/${P}/provenance.json"
    if [ -f "$PROV" ]; then
        cp "$PROV" "$RELEASE_DIR/provenance/${P}_provenance.json"
    fi
done

# Copy license
cp LICENSE "$RELEASE_DIR/" 2>/dev/null || true

echo ""
echo "Release pack at: $RELEASE_DIR/"
ls -la "$RELEASE_DIR/"
echo "=================================================="
