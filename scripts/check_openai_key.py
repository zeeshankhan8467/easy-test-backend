#!/usr/bin/env python3
"""
Verify OPENAI_API_KEY works with the OpenAI Chat Completions API.

Usage (from easy-test-backend/):
  python scripts/check_openai_key.py

Uses the same .env as Django: easy-test-backend/.env
Does not print your secret key.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def main() -> int:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        print("ERROR: OPENAI_API_KEY is missing or empty after loading .env")
        print(f"       Expected file: {ROOT / '.env'}")
        return 1

    print(f"Key loaded: yes (length {len(api_key)}, starts with {api_key[:7]}...)")

    model = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
    base_url = (os.getenv("OPENAI_BASE_URL") or "").strip()

    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package not installed. Run: pip install openai")
        return 1

    client_kwargs: dict = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url.rstrip("/")
        print(f"Using OPENAI_BASE_URL: {base_url[:40]}...")

    client = OpenAI(**client_kwargs)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You reply with one word only."},
                {"role": "user", "content": 'Reply with exactly the word: ok'},
            ],
            max_tokens=10,
            temperature=0,
        )
    except Exception as e:
        print("FAILED: OpenAI returned an error (key may be invalid, model wrong, or billing issue).")
        print(f"       {type(e).__name__}: {e}")
        return 2

    text = (response.choices[0].message.content or "").strip()
    print(f"SUCCESS: Chat Completions works.")
    print(f"         Model: {model}")
    print(f"         Sample reply: {text!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
