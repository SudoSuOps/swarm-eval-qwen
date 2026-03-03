#!/usr/bin/env python3
"""
Validate training pairs against the data contract.

Checks:
1. Schema validation (pair.schema.json)
2. Assistant content is valid judge JSON (verdict + scores + reasoning)
3. No duplicate fingerprints
4. Pass/fail distribution within expected range
5. No eval fingerprints in train set (leakage check)

Usage:
    python3 validate_pairs.py --train /path/to/train.jsonl --eval /path/to/eval.jsonl
    python3 validate_pairs.py --train /path/to/train.jsonl --expected-pass-pct 70
"""

import json, argparse, sys
from pathlib import Path
from collections import Counter

REQUIRED_CRITERIA = {"accuracy", "completeness", "structure", "relevance", "sft_quality"}


def validate_pair(pair: dict, idx: int) -> list[str]:
    """Validate a single pair. Returns list of error strings."""
    errors = []

    # Check messages exist
    msgs = pair.get("messages")
    if not msgs or not isinstance(msgs, list):
        errors.append(f"pair {idx}: missing or invalid 'messages'")
        return errors

    if len(msgs) < 2:
        errors.append(f"pair {idx}: need at least 2 messages, got {len(msgs)}")

    # Check roles
    roles = [m.get("role") for m in msgs]
    if "assistant" not in roles:
        errors.append(f"pair {idx}: no assistant message")

    for i, m in enumerate(msgs):
        if m.get("role") not in ("system", "user", "assistant"):
            errors.append(f"pair {idx} msg {i}: invalid role '{m.get('role')}'")
        if not m.get("content"):
            errors.append(f"pair {idx} msg {i}: empty content")

    # Check metadata
    meta = pair.get("metadata", {})
    if not meta.get("fingerprint"):
        errors.append(f"pair {idx}: missing metadata.fingerprint")
    if not meta.get("task_type") and not meta.get("specialty"):
        errors.append(f"pair {idx}: missing metadata.task_type or specialty")

    # Validate assistant JSON content
    asst = next((m["content"] for m in msgs if m.get("role") == "assistant"), None)
    if asst:
        try:
            ev = json.loads(asst)
        except json.JSONDecodeError:
            errors.append(f"pair {idx}: assistant content is not valid JSON")
            return errors

        if ev.get("verdict") not in ("PASS", "FAIL"):
            errors.append(f"pair {idx}: verdict must be PASS or FAIL, got '{ev.get('verdict')}'")

        scores = ev.get("scores", {})
        missing = REQUIRED_CRITERIA - set(scores.keys())
        if missing:
            errors.append(f"pair {idx}: missing score criteria: {missing}")

        for c in REQUIRED_CRITERIA:
            if c in scores:
                v = scores[c]
                if not isinstance(v, (int, float)) or v < 1 or v > 5:
                    errors.append(f"pair {idx}: score.{c} = {v} (must be 1-5)")

        if not ev.get("reasoning"):
            errors.append(f"pair {idx}: missing reasoning")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate training pairs")
    parser.add_argument("--train", required=True, help="Path to train JSONL")
    parser.add_argument("--eval", help="Path to eval JSONL (for leakage check)")
    parser.add_argument("--expected-pass-pct", type=float, default=None,
                        help="Expected PASS percentage (e.g. 70 for 70%%)")
    parser.add_argument("--tolerance", type=float, default=5.0,
                        help="Tolerance on pass/fail distribution (default 5%%)")
    args = parser.parse_args()

    train_path = Path(args.train)
    pairs = []
    print(f"Loading {train_path}...")
    with open(train_path) as f:
        for line in f:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    print(f"  Loaded {len(pairs)} pairs")

    # Schema validation
    all_errors = []
    fingerprints = []
    verdicts = Counter()
    for i, p in enumerate(pairs):
        errs = validate_pair(p, i)
        all_errors.extend(errs)
        fp = p.get("metadata", {}).get("fingerprint", "")
        if fp:
            fingerprints.append(fp)
        asst = next((m["content"] for m in p.get("messages", []) if m.get("role") == "assistant"), "{}")
        try:
            verdicts[json.loads(asst).get("verdict", "UNKNOWN")] += 1
        except Exception:
            verdicts["PARSE_ERROR"] += 1

    # Duplicate check
    fp_counts = Counter(fingerprints)
    dupes = {fp: c for fp, c in fp_counts.items() if c > 1}
    if dupes:
        all_errors.append(f"DUPLICATE FINGERPRINTS: {len(dupes)} fingerprints appear >1 time")
        for fp, c in list(dupes.items())[:5]:
            all_errors.append(f"  {fp[:24]}... appears {c} times")

    # Distribution check
    if args.expected_pass_pct is not None:
        total = sum(verdicts.values())
        actual_pass_pct = 100 * verdicts.get("PASS", 0) / total if total else 0
        diff = abs(actual_pass_pct - args.expected_pass_pct)
        if diff > args.tolerance:
            all_errors.append(
                f"DISTRIBUTION: PASS is {actual_pass_pct:.1f}% "
                f"(expected {args.expected_pass_pct}% +/- {args.tolerance}%)"
            )

    # Leakage check
    if args.eval:
        eval_path = Path(args.eval)
        eval_fps = set()
        with open(eval_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    p = json.loads(line)
                    fp = p.get("metadata", {}).get("fingerprint", "")
                    if fp:
                        eval_fps.add(fp)
        train_fps = set(fingerprints)
        leaked = train_fps & eval_fps
        if leaked:
            all_errors.append(f"LEAKAGE: {len(leaked)} eval fingerprints found in train set")
            for fp in list(leaked)[:5]:
                all_errors.append(f"  {fp[:24]}...")
        else:
            print(f"  Leakage check: CLEAN (0 overlaps, {len(eval_fps)} eval fingerprints)")

    # Report
    print(f"\n{'='*50}")
    print(f"Validation Report")
    print(f"{'='*50}")
    print(f"  Pairs:       {len(pairs)}")
    print(f"  Verdicts:    {dict(verdicts)}")
    print(f"  Fingerprints: {len(fingerprints)} ({len(set(fingerprints))} unique)")
    print(f"  Duplicates:  {len(dupes)}")
    print(f"  Errors:      {len(all_errors)}")

    if all_errors:
        print(f"\nERRORS:")
        for e in all_errors[:50]:
            print(f"  {e}")
        if len(all_errors) > 50:
            print(f"  ... and {len(all_errors) - 50} more")
        print(f"\nRESULT: FAIL")
        sys.exit(1)
    else:
        print(f"\nRESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
