"""File hashing utilities."""
import hashlib
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    """Compute SHA256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_string(s: str) -> str:
    """Compute SHA256 of a string."""
    return hashlib.sha256(s.encode()).hexdigest()
