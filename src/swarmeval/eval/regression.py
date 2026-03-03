#!/usr/bin/env python3
"""
Regression gate — compare Phase N vs Phase N-1.

Rules:
- Must improve or hold core metrics
- Must not regress adversarial beyond threshold
- Must reduce known failure categories OR prove tradeoff acceptable
- If gate fails: do not advance phases

Usage:
    python3 -m swarmeval.eval.regression \
        --current results/.../phase2/eval/metrics.json \
        --baseline results/.../phase1/eval/metrics.json \
        --threshold 2.0
"""

import json, argparse, sys
from pathlib import Path


def load_metrics(path: str) -> dict:
    return json.loads(Path(path).read_text())


def compare(current: dict, baseline: dict, threshold: float = 2.0) -> dict:
    """Compare current vs baseline metrics. Threshold = max allowed regression in pct points."""

    report = {
        "current_suite": current.get("suite"),
        "baseline_suite": baseline.get("suite"),
        "deltas": {},
        "regressions": [],
        "improvements": [],
        "gate": "PASS",
    }

    # Compare key metrics
    metrics_to_check = [
        ("json_valid_pct", "higher_better"),
        ("pass_precision", "higher_better"),
        ("pass_recall", "higher_better"),
        ("fail_precision", "higher_better"),
        ("fail_recall", "higher_better"),
        ("under_reject_rate", "lower_better"),
        ("over_reject_rate", "lower_better"),
        ("score_mae", "lower_better"),
    ]

    for metric, direction in metrics_to_check:
        c_val = current.get(metric) or current.get("confusion", {}).get(metric)
        b_val = baseline.get(metric) or baseline.get("confusion", {}).get(metric)

        if c_val is None or b_val is None:
            continue

        delta = c_val - b_val
        report["deltas"][metric] = {
            "current": c_val,
            "baseline": b_val,
            "delta": round(delta, 3),
        }

        # Check regression
        if direction == "higher_better" and delta < -threshold:
            report["regressions"].append(f"{metric}: {b_val} -> {c_val} (regressed {abs(delta):.2f})")
        elif direction == "lower_better" and delta > threshold:
            report["regressions"].append(f"{metric}: {b_val} -> {c_val} (regressed {delta:.2f})")
        elif direction == "higher_better" and delta > 0:
            report["improvements"].append(f"{metric}: {b_val} -> {c_val} (+{delta:.2f})")
        elif direction == "lower_better" and delta < 0:
            report["improvements"].append(f"{metric}: {b_val} -> {c_val} ({delta:.2f})")

    if report["regressions"]:
        report["gate"] = "FAIL"

    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True, help="Current phase metrics.json")
    parser.add_argument("--baseline", required=True, help="Baseline phase metrics.json")
    parser.add_argument("--threshold", type=float, default=2.0,
                        help="Max allowed regression in percentage points")
    parser.add_argument("--output", help="Output path for delta report")
    args = parser.parse_args()

    current = load_metrics(args.current)
    baseline = load_metrics(args.baseline)
    report = compare(current, baseline, args.threshold)

    print(f"\n{'='*60}")
    print(f"Regression Gate")
    print(f"{'='*60}")
    print(f"  Current:  {args.current}")
    print(f"  Baseline: {args.baseline}")
    print(f"  Threshold: {args.threshold}% max regression")

    print(f"\n  Deltas:")
    for metric, d in report["deltas"].items():
        sign = "+" if d["delta"] >= 0 else ""
        print(f"    {metric:<22} {d['baseline']:>8} -> {d['current']:>8}  ({sign}{d['delta']})")

    if report["improvements"]:
        print(f"\n  Improvements:")
        for imp in report["improvements"]:
            print(f"    {imp}")

    if report["regressions"]:
        print(f"\n  REGRESSIONS:")
        for reg in report["regressions"]:
            print(f"    {reg}")

    print(f"\n  GATE: {report['gate']}")
    print(f"{'='*60}")

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(report, indent=2))
        print(f"  Report -> {args.output}")

    sys.exit(0 if report["gate"] == "PASS" else 1)


if __name__ == "__main__":
    main()
