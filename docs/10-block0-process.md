# Block-0 Process

## The Build Cycle

```
Block-0: Train fresh on sealed data
    |
Evaluate: Judge runs acceptance tests
    |
PASS --> Block-0 IS v1. Seal and ship.
FAIL --> Diagnose. Targeted fine-tune. That becomes v1.
```

Block-0 is not a rough draft. It is a full, clean, sealed training run.

## Phase Progression

| Phase | Purpose | Data | Builds On |
|-------|---------|------|-----------|
| Phase 1 | Identity lock | PASS-only pairs | Base model |
| Phase 2 | FAIL recognition | PASS + FAIL pairs (70/30) | Phase 1 merged |
| Phase 3 | Specialty reinforcement | Targeted from Phase 2 failures | Phase 2 merged |

Each phase:
1. Lock dataset manifest (hashes, counts, splits)
2. Validate schema + leakage
3. Train with frozen config
4. Eval all three suites (core, edges, adversarial)
5. Regression gate against Phase N-1
6. Advance or stop

## Regression Gate Rules

- Must improve or hold core metrics
- Must not regress adversarial beyond threshold
- Must reduce known failure categories OR prove acceptable tradeoff
- If gate fails: you don't advance phases

## Seal Process (Block-0 Final)

1. SHA256 all merged model shards
2. Provenance JSON (full chain: base -> P1 -> P2 -> P3 -> final)
3. All eval reports bundled
4. Push to R2: `sb-models/{model_id}/`
5. Supabase `model_builds` entry
6. GGUF quantization (Q4_K_M)
7. NAS backup
8. Release pack generated
