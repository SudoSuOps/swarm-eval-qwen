#!/usr/bin/env bash
set -euo pipefail

# Merge LoRA adapter after training.
# Usage: bash scripts/04_merge.sh /path/to/adapter /path/to/base /path/to/output

echo "Merge is handled by the training script (Unsloth auto-merge)."
echo "This script validates the merged output."
echo ""

MERGED="${1:?Usage: $0 MERGED_DIR}"

if [ ! -d "$MERGED" ]; then
    echo "ERROR: Merged directory not found: $MERGED"
    exit 1
fi

echo "Merged model: $MERGED"
echo ""

# Count shards
SHARDS=$(ls "$MERGED"/model.safetensors*.safetensors 2>/dev/null | wc -l)
echo "  Shards: $SHARDS"

# Check config
if [ -f "$MERGED/config.json" ]; then
    echo "  config.json: OK"
else
    echo "  config.json: MISSING"
fi

# Check tokenizer
if [ -f "$MERGED/tokenizer_config.json" ]; then
    echo "  tokenizer_config.json: OK"
else
    echo "  tokenizer_config.json: MISSING"
fi

# Total size
SIZE=$(du -sh "$MERGED" | awk '{print $1}')
echo "  Total size: $SIZE"

# SHA256 each shard
echo ""
echo "  Shard hashes:"
for F in "$MERGED"/model.safetensors*.safetensors; do
    SHA=$(sha256sum "$F" | awk '{print $1}')
    echo "    $(basename $F): ${SHA:0:16}..."
done
