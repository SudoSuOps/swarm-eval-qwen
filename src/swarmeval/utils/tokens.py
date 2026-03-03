"""Token counting and analysis utilities."""
import json


def count_tokens(tokenizer, text: str) -> int:
    """Count tokens in a string."""
    return len(tokenizer.encode(text, add_special_tokens=False))


def pair_token_stats(tokenizer, pair: dict) -> dict:
    """Get token statistics for a training pair."""
    msgs = pair.get("messages", [])
    stats = {"system": 0, "user": 0, "assistant": 0, "total": 0}
    for m in msgs:
        role = m.get("role", "")
        n = count_tokens(tokenizer, m.get("content", ""))
        if role in stats:
            stats[role] += n
        stats["total"] += n
    return stats


def assistant_json_tokens(tokenizer, pair: dict) -> int:
    """Count tokens in the assistant JSON output."""
    for m in pair.get("messages", []):
        if m.get("role") == "assistant":
            return count_tokens(tokenizer, m.get("content", ""))
    return 0
