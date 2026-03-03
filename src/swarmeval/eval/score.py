"""Scoring functions for SwarmJudge eval."""
import json
from collections import Counter

CRITERIA = ["accuracy", "completeness", "structure", "relevance", "sft_quality"]


def parse_output(text: str) -> dict | None:
    """Extract JSON from model output, handling think blocks and stop tokens."""
    text = text.strip()
    if "<think>" in text:
        think_end = text.find("</think>")
        if think_end >= 0:
            text = text[think_end + len("</think>"):].strip()
    if "<|im_end|>" in text:
        text = text[:text.index("<|im_end|>")].strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except Exception:
            pass
    return None


def score_pair(pred: dict | None, gold: dict) -> dict:
    """Score a single prediction against gold label."""
    result = {
        "json_valid": pred is not None,
        "verdict_match": False,
        "pred_verdict": None,
        "gold_verdict": gold.get("verdict", "").upper(),
        "score_mae": None,
        "score_mae_by_criterion": {},
    }
    if pred is None:
        return result

    result["pred_verdict"] = pred.get("verdict", "").upper()
    result["verdict_match"] = result["gold_verdict"] == result["pred_verdict"]

    gold_scores = gold.get("scores", {})
    pred_scores = pred.get("scores", {})
    maes = []
    for c in CRITERIA:
        if c in gold_scores and c in pred_scores:
            try:
                mae = abs(float(pred_scores[c]) - float(gold_scores[c]))
                maes.append(mae)
                result["score_mae_by_criterion"][c] = mae
            except (TypeError, ValueError):
                pass
    if maes:
        result["score_mae"] = sum(maes) / len(maes)

    return result


def build_confusion(results: list) -> dict:
    """Build confusion matrix from scored results."""
    tp_pass = sum(1 for r in results if r["gold_verdict"] == "PASS" and r["pred_verdict"] == "PASS")
    fp_pass = sum(1 for r in results if r["gold_verdict"] == "FAIL" and r["pred_verdict"] == "PASS")
    fn_pass = sum(1 for r in results if r["gold_verdict"] == "PASS" and r["pred_verdict"] != "PASS")
    tp_fail = sum(1 for r in results if r["gold_verdict"] == "FAIL" and r["pred_verdict"] == "FAIL")
    fp_fail = sum(1 for r in results if r["gold_verdict"] == "PASS" and r["pred_verdict"] == "FAIL")
    fn_fail = sum(1 for r in results if r["gold_verdict"] == "FAIL" and r["pred_verdict"] != "FAIL")

    total_gold_pass = sum(1 for r in results if r["gold_verdict"] == "PASS")
    total_gold_fail = sum(1 for r in results if r["gold_verdict"] == "FAIL")

    pass_prec = tp_pass / (tp_pass + fp_pass) if (tp_pass + fp_pass) > 0 else 0
    pass_rec = tp_pass / (tp_pass + fn_pass) if (tp_pass + fn_pass) > 0 else 0
    fail_prec = tp_fail / (tp_fail + fp_fail) if (tp_fail + fp_fail) > 0 else 0
    fail_rec = tp_fail / (tp_fail + fn_fail) if (tp_fail + fn_fail) > 0 else 0

    under_reject = fp_pass / total_gold_fail if total_gold_fail > 0 else 0
    over_reject = fp_fail / total_gold_pass if total_gold_pass > 0 else 0

    return {
        "matrix": {
            "tp_pass": tp_pass, "fp_pass": fp_pass, "fn_pass": fn_pass,
            "tp_fail": tp_fail, "fp_fail": fp_fail, "fn_fail": fn_fail,
        },
        "counts": {"gold_pass": total_gold_pass, "gold_fail": total_gold_fail},
        "pass_precision": round(pass_prec * 100, 2),
        "pass_recall": round(pass_rec * 100, 2),
        "fail_precision": round(fail_prec * 100, 2),
        "fail_recall": round(fail_rec * 100, 2),
        "under_reject_rate": round(under_reject * 100, 2),
        "over_reject_rate": round(over_reject * 100, 2),
    }


def check_acceptance(confusion: dict, json_valid_pct: float,
                     score_mae: float | None, thresholds: dict) -> dict:
    """Check eval results against acceptance criteria."""
    checks = {}
    checks["json_valid"] = {
        "threshold": thresholds.get("json_valid_pct", 95),
        "actual": json_valid_pct,
        "pass": json_valid_pct >= thresholds.get("json_valid_pct", 95),
    }
    if "pass_precision" in thresholds:
        checks["pass_precision"] = {
            "threshold": thresholds["pass_precision"],
            "actual": confusion["pass_precision"],
            "pass": confusion["pass_precision"] >= thresholds["pass_precision"],
        }
    if "fail_precision" in thresholds:
        checks["fail_precision"] = {
            "threshold": thresholds["fail_precision"],
            "actual": confusion["fail_precision"],
            "pass": confusion["fail_precision"] >= thresholds["fail_precision"],
        }
    if "under_reject_rate" in thresholds:
        checks["under_reject_rate"] = {
            "threshold": thresholds["under_reject_rate"],
            "actual": confusion["under_reject_rate"],
            "pass": confusion["under_reject_rate"] <= thresholds["under_reject_rate"],
        }
    if "over_reject_rate" in thresholds:
        checks["over_reject_rate"] = {
            "threshold": thresholds["over_reject_rate"],
            "actual": confusion["over_reject_rate"],
            "pass": confusion["over_reject_rate"] <= thresholds["over_reject_rate"],
        }
    if "score_mae_max" in thresholds:
        checks["score_mae"] = {
            "threshold": thresholds["score_mae_max"],
            "actual": score_mae,
            "pass": (score_mae is not None and score_mae <= thresholds["score_mae_max"]),
        }
    checks["all_pass"] = all(
        c["pass"] for c in checks.values() if isinstance(c, dict) and "pass" in c
    )
    return checks
