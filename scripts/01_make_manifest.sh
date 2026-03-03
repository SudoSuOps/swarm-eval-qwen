#!/usr/bin/env bash
set -euo pipefail

# Generate dataset manifest with file hashes.
# Usage: bash scripts/01_make_manifest.sh /path/to/train.jsonl swarmjudge-9b-cre-b0 phase2

TRAIN_PATH="${1:?Usage: $0 TRAIN_PATH MODEL PHASE}"
MODEL="${2:?Usage: $0 TRAIN_PATH MODEL PHASE}"
PHASE="${3:?Usage: $0 TRAIN_PATH MODEL PHASE}"

MANIFEST_DIR="datasets/manifests/${MODEL}"
FINGERPRINT_DIR="datasets/fingerprints"
mkdir -p "$MANIFEST_DIR" "$FINGERPRINT_DIR"

echo "Generating manifest for ${MODEL} ${PHASE}..."
echo "  Train: $TRAIN_PATH"

# SHA256
TRAIN_SHA=$(sha256sum "$TRAIN_PATH" | awk '{print $1}')
TRAIN_SIZE=$(stat -c %s "$TRAIN_PATH" 2>/dev/null || stat -f %z "$TRAIN_PATH")
TRAIN_LINES=$(wc -l < "$TRAIN_PATH")

echo "  SHA256: $TRAIN_SHA"
echo "  Size:   $TRAIN_SIZE bytes"
echo "  Lines:  $TRAIN_LINES"

# Save fingerprint
echo "$TRAIN_SHA  $(basename $TRAIN_PATH)" > "$FINGERPRINT_DIR/${PHASE}.sha256.txt"

echo ""
echo "Fingerprint written to $FINGERPRINT_DIR/${PHASE}.sha256.txt"
echo "Update $MANIFEST_DIR/${PHASE}.manifest.json with these values."
