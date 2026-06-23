"""
openai_helper.py — Shared utilities for image-gen scripts that may
upgrade to LLM-driven content later.

The .env file in repo root has:
    OPEN_API_KEY=sk-...        (user's actual variable name)
We accept both that and the canonical OPENAI_API_KEY.
"""
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"


def load_env() -> None:
    """Tiny .env loader (no dependency on python-dotenv).
    Strips whitespace from key and value, supports KEY=VALUE."""
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        # User's .env uses "OPEN_API_KEY" (with possible trailing space).
        # Normalize and also expose canonical OPENAI_API_KEY for OpenAI SDK.
        if k:
            os.environ.setdefault(k, v)


def get_openai_key() -> str | None:
    """Return the OpenAI API key from environment, accepting either
    the canonical OPENAI_API_KEY or the user's OPEN_API_KEY name."""
    load_env()
    return (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("OPEN_API_KEY")
        or os.environ.get("OPEN_API_KEY ")  # account for trailing space
    )


def ensure_canonical_key() -> bool:
    """If OpenAI SDK is installed and a key is found under any name,
    set OPENAI_API_KEY so the SDK picks it up automatically.
    Returns True if a key is now available, False otherwise."""
    k = get_openai_key()
    if k:
        os.environ["OPENAI_API_KEY"] = k
        return True
    return False
