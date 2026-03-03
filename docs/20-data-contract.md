# Data Contract

## Non-Negotiables

Every training/eval record must validate against schemas in `data_contract/schema/`.

## Pair Schema

Every training pair (`pair.schema.json`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| messages | array | yes | Chat-format messages (system, user, assistant) |
| metadata.fingerprint | string | yes | Dedup key |
| metadata.task_type | string | yes | CRE specialty or task category |
| metadata.source | string | yes | Cook run ID or data source |
| metadata.created_at | string | yes | ISO 8601 timestamp |

The assistant message must contain valid JSON with:
- `verdict`: "PASS" or "FAIL"
- `scores`: object with all 5 criteria (accuracy, completeness, structure, relevance, sft_quality)
- `reasoning`: non-empty string or object

## Eval Case Schema

Every eval fixture (`evalcase.schema.json`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Unique fixture ID |
| prompt | array | yes | Chat messages (system + user) |
| expected_verdict | string | yes | "PASS" or "FAIL" |
| rubric | object | yes | Expected score ranges per criterion |
| category | string | yes | Test category (core/edge/adversarial) |
| difficulty | string | yes | easy/medium/hard |
| gold_rationale | string | no | Why this verdict is correct |
| tags | array | yes | Searchable labels |

## Manifest Requirements

Each phase dataset has a manifest (`datasets/manifests/`):

| Field | Required | Description |
|-------|----------|-------------|
| dataset_location | yes | R2 path or NAS path |
| files | yes | List of {name, size_bytes, sha256} |
| total_pairs | yes | Count |
| pass_count | yes | PASS verdict count |
| fail_count | yes | FAIL verdict count |
| dedup_strategy | yes | How duplicates were removed |
| schema_version | yes | Which pair schema version |
| created_utc | yes | When manifest was generated |
| source_runs | yes | Which cook runs produced this data |

## Validation Checks

Run before every training:

1. Schema validation (all pairs match pair.schema.json)
2. Pass/fail distribution check (within expected range)
3. Leakage check (no eval fingerprints in train set)
4. Token length histogram sanity (no outliers beyond seq_len)
5. Dedup verification (no duplicate fingerprints)
