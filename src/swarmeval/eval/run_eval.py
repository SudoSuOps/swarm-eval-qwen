#!/usr/bin/env python3
"""
SwarmJudge Eval Runner — Qwen-aligned inference.

Reads config YAML, loads model with correct sampling parameters,
runs eval suites, writes metrics + failures + confusion.

Usage:
    python3 -m swarmeval.eval.run_eval --config configs/eval/suites/cre_core.yaml \
        --model-config configs/models/swarmjudge-9b-cre-b0/phase2.yaml \
        --sampling-config configs/models/swarmjudge-9b-cre-b0/sampling.yaml
    python3 -m swarmeval.eval.run_eval ... --dry-run
    python3 -m swarmeval.eval.run_eval ... --baseline
"""

import json, argparse, time, os, sys
from pathlib import Path
from datetime import datetime, timezone

import yaml

from swarmeval.eval.score import parse_output, score_pair, build_confusion, check_acceptance, CRITERIA
from swarmeval.utils.seeds import set_seed


def load_yaml(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def run(model_path: str, eval_path: str, sampling: dict, suite_config: dict,
        output_dir: str, gpu_device: str = "cuda:1", family: str = "qwen3_5",
        dry_run: bool = False):
    """Run eval on a single suite."""
    set_seed(42)

    suite_name = suite_config.get("suite", "unknown")
    acceptance = suite_config.get("acceptance", {})

    print(f"\n{'='*60}")
    print(f"Eval Suite: {suite_name}")
    print(f"{'='*60}")
    print(f"Model:      {model_path}")
    print(f"Eval data:  {eval_path}")
    print(f"Sampling:   temp={sampling['temperature']} top_p={sampling['top_p']} "
          f"top_k={sampling['top_k']} pp={sampling.get('presence_penalty', 'n/a')}")
    print(f"do_sample:  {sampling['do_sample']}")

    # Load eval data
    pairs = [json.loads(l) for l in Path(eval_path).read_text().splitlines() if l.strip()]
    print(f"Samples:    {len(pairs)}")

    if dry_run:
        print("[DRY RUN] Config validated. No GPU work.")
        return None

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    os.environ.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype=torch.bfloat16,
        device_map=gpu_device, trust_remote_code=True,
    )
    model.eval()

    eos_ids = sampling.get("eos_token_id")
    if eos_ids is None:
        # Auto-detect from tokenizer
        eos_ids = []
        for tok_str in ["<|im_end|>", "<|endoftext|>"]:
            ids = tokenizer.encode(tok_str, add_special_tokens=False)
            if ids:
                eos_ids.append(ids[0])

    # Prepare prompts + gold
    gold_labels = []
    prompts = []
    for p in pairs:
        msgs = p["messages"]
        prompt_msgs = [m for m in msgs if m["role"] != "assistant"]
        gold_asst = next((m["content"] for m in msgs if m["role"] == "assistant"), "{}")
        try:
            gold_labels.append(json.loads(gold_asst))
        except Exception:
            gold_labels.append({})

        # Qwen3.5 <=9B: think off by default. Qwen3: must disable.
        if family == "qwen3":
            text = tokenizer.apply_chat_template(
                prompt_msgs, tokenize=False,
                add_generation_prompt=True, enable_thinking=False,
            )
        else:
            text = tokenizer.apply_chat_template(
                prompt_msgs, tokenize=False, add_generation_prompt=True,
            )
        prompts.append(text)

    # Inference — single sample, no batch padding
    print(f"\nRunning inference ({len(prompts)} samples)...")
    t_start = time.time()
    raw_outputs = []
    gen_counts = []

    for i, prompt in enumerate(prompts):
        enc = tokenizer(prompt, return_tensors="pt", truncation=True,
                        max_length=4096).to(gpu_device)
        prompt_len = enc["input_ids"].shape[1]

        with torch.no_grad():
            out = model.generate(
                **enc,
                max_new_tokens=sampling.get("max_new_tokens", 512),
                do_sample=sampling["do_sample"],
                temperature=sampling["temperature"],
                top_p=sampling["top_p"],
                top_k=sampling["top_k"],
                repetition_penalty=sampling.get("repetition_penalty", 1.0),
                eos_token_id=eos_ids if eos_ids else None,
                pad_token_id=tokenizer.pad_token_id,
            )

        gen = out[0][prompt_len:]
        raw_outputs.append(tokenizer.decode(gen, skip_special_tokens=False))
        gen_counts.append(len(gen))

        if (i + 1) % 10 == 0 or i == 0:
            elapsed = time.time() - t_start
            rate = (i + 1) / elapsed
            eta = (len(prompts) - i - 1) / rate
            print(f"  {i+1}/{len(prompts)}  ({elapsed:.0f}s, ~{eta:.0f}s ETA)", flush=True)

    total_time = time.time() - t_start
    avg_gen = sum(gen_counts) / len(gen_counts) if gen_counts else 0
    print(f"Done: {total_time:.0f}s ({total_time/len(prompts):.1f}s/sample, {avg_gen:.0f} avg tokens)")

    # Score
    results = []
    for idx, (text, gold) in enumerate(zip(raw_outputs, gold_labels)):
        pred = parse_output(text)
        sc = score_pair(pred, gold)
        results.append({
            "index": idx, "gold": gold, "pred": pred,
            "scores": sc, "raw": text[:1000], "gen_tokens": gen_counts[idx],
        })

    # Aggregate
    scored = [r["scores"] for r in results]
    n = len(scored)
    json_valid = sum(1 for s in scored if s["json_valid"])
    json_valid_pct = round(100 * json_valid / n, 2)
    maes = [s["score_mae"] for s in scored if s["score_mae"] is not None]
    avg_mae = round(sum(maes) / len(maes), 3) if maes else None

    criterion_maes = {c: [] for c in CRITERIA}
    for s in scored:
        for c, v in s.get("score_mae_by_criterion", {}).items():
            criterion_maes[c].append(v)
    criterion_avg = {c: round(sum(vs)/len(vs), 3) if vs else None for c, vs in criterion_maes.items()}

    confusion = build_confusion(scored)
    accept = check_acceptance(confusion, json_valid_pct, avg_mae, acceptance)

    # Print
    print(f"\n{'='*60}")
    print(f"RESULTS — {suite_name}")
    print(f"{'='*60}")
    print(f"  JSON valid:        {json_valid}/{n} ({json_valid_pct}%)")
    print(f"  Score MAE:         {avg_mae}")
    for c in CRITERIA:
        print(f"    {c:<20} {criterion_avg[c]}")
    print(f"  PASS prec/rec:     {confusion['pass_precision']}% / {confusion['pass_recall']}%")
    print(f"  FAIL prec/rec:     {confusion['fail_precision']}% / {confusion['fail_recall']}%")
    print(f"  Under-reject:      {confusion['under_reject_rate']}%")
    print(f"  Over-reject:       {confusion['over_reject_rate']}%")
    print(f"\n  Acceptance:")
    for k, v in accept.items():
        if isinstance(v, dict):
            s = "PASS" if v["pass"] else "FAIL"
            print(f"    {k:<22} {v['actual']:>8} (>= {v['threshold']}) [{s}]")
    print(f"  OVERALL: {'PASS' if accept['all_pass'] else 'FAIL'}")

    # Save
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "suite": suite_name,
        "model": model_path,
        "n_samples": n,
        "inference_sec": round(total_time, 1),
        "sampling": sampling,
        "json_valid_pct": json_valid_pct,
        "score_mae": avg_mae,
        "criterion_mae": criterion_avg,
        "confusion": confusion,
        "acceptance": accept,
    }
    (out / "metrics.json").write_text(json.dumps(report, indent=2))

    fails = [r for r in results if not r["scores"]["verdict_match"] or not r["scores"]["json_valid"]]
    if fails:
        with open(out / "failures.jsonl", "w") as f:
            for r in fails:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Confusion CSV
    m = confusion["matrix"]
    with open(out / "confusion.csv", "w") as f:
        f.write("gold,pred_PASS,pred_FAIL\n")
        f.write(f"PASS,{m['tp_pass']},{m['fp_fail']}\n")
        f.write(f"FAIL,{m['fp_pass']},{m['tp_fail']}\n")

    with open(out / "samples.jsonl", "w") as f:
        for r in results[:20]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n  Saved to {out}/")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Suite config YAML")
    parser.add_argument("--model-config", required=True, help="Model phase config YAML")
    parser.add_argument("--sampling-config", required=True, help="Sampling config YAML")
    parser.add_argument("--gpu", default="cuda:1")
    parser.add_argument("--baseline", action="store_true", help="Use base model from phase config")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    suite = load_yaml(args.config)
    model_cfg = load_yaml(args.model_config)
    sampling_cfg = load_yaml(args.sampling_config)

    model_path = model_cfg["artifacts"]["merged"] if not args.baseline else model_cfg["base_model"]["path"]
    eval_path = suite["evalset"]
    family = model_cfg.get("base_model", {}).get("family", "qwen3_5")
    sampling = sampling_cfg.get("judge", sampling_cfg.get("eval_deterministic", {}))

    phase = model_cfg["phase"]
    model_id = model_cfg["model_id"]
    out_dir = f"results/{model_id}/phase{phase}/eval"

    run(model_path, eval_path, sampling, suite,
        out_dir, gpu_device=args.gpu, family=family, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
