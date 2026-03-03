# Incident Playbook

## Eval Failures

### JSON invalid rate > 5%
1. Check sampling parameters match `sampling.yaml`
2. Check `max_new_tokens` — judge JSON is ~400 tokens, need 512 minimum
3. Check EOS token IDs match model family
4. If Qwen3: verify `enable_thinking=False` is set
5. Inspect raw output in `eval_samples.jsonl` — look for truncation or think blocks

### Under-reject rate > 10%
Model is letting bad work through. This is the critical failure mode.
1. Inspect `failures.jsonl` — categorize what types of FAIL it misses
2. Check if Phase 2 training had enough FAIL examples in that category
3. Generate targeted fix pairs for Phase 3 from failure categories
4. Do NOT just add more data randomly — target the weakness

### Over-reject rate > 15%
Model is too strict — rejecting good work.
1. Inspect false FAILs in `failures.jsonl` — is the model right and the label wrong?
2. Check for label noise in training data
3. If labels are correct: model may need more PASS diversity in that category

### Score MAE > 0.5
Scores are drifting from gold labels.
1. Check per-criterion breakdown — which criterion is worst?
2. Check if it's systematic (always +1 or -1) or random
3. Systematic drift = calibration issue, fixable with targeted data
4. Random drift = model hasn't learned scoring rubric

## Training Failures

### Loss not decreasing after warmup
1. Check learning rate — too high or too low?
2. Check data quality — schema validation pass?
3. Check packing — without `packing=True`, padding dominates and loss appears flat
4. For Qwen3.5: verify bf16 LoRA, NOT QLoRA

### Loss spike mid-training
1. Check for bad data (corrupt JSON, empty fields)
2. Check gradient norm — if spiking, reduce LR
3. Do NOT restart from scratch — resume from last checkpoint

### OOM during training
1. Reduce batch_size first (keep grad_accum high to maintain effective batch)
2. Reduce max_seq_length
3. Enable gradient checkpointing: `use_gradient_checkpointing='unsloth'`
4. Never use QLoRA for Qwen3.5 as a VRAM workaround — use smaller batch instead

## Infrastructure

### GPU process won't die
```bash
ssh swarmrails "kill -9 <PID>"
# If that fails:
ssh swarmrails "nvidia-smi --gpu-reset -i <GPU_INDEX>"
```

### Wrong GPU selected
Always set:
```bash
CUDA_DEVICE_ORDER=PCI_BUS_ID
CUDA_VISIBLE_DEVICES=0  # 3090 Ti
CUDA_VISIBLE_DEVICES=1  # Blackwell
```

### Tokenizer mismatch after merge
Run `scripts/02_validate_data.sh` tokenizer check.
Compare vocab_size, eos_token_id, special tokens between phases.
If mismatch: merge corrupted the tokenizer. Re-merge from adapter + base.
