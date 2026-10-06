"""Tiny Groq client (OpenAI-compatible API). Returns parsed JSON, retries, and picks a working model by itself."""
import json
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE = "https://api.groq.com/openai/v1"
CONFIGURED = [m for m in (os.getenv("GROQ_MODEL"), os.getenv("GROQ_FALLBACK_MODEL")) if m]
# Model names change over time, so if the configured ones fail we ask Groq what exists
# and prefer these families (first match wins).
PREFER = ("llama-3.3-70b", "gpt-oss-120b", "llama-4", "qwen", "llama-3.1-8b", "gpt-oss-20b", "llama")
SKIP = ("whisper", "tts", "guard", "embed", "playai", "orpheus", "prompt-guard", "safeguard")

_models = None


def _key():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise SystemExit("GROQ_API_KEY not found. Copy .env.example to .env and paste your key.")
    return key


def available_models():
    """Chat models Groq says this key can use, best first. Cached."""
    global _models
    if _models is None:
        r = httpx.get(f"{BASE}/models", headers={"Authorization": f"Bearer {_key()}"}, timeout=30)
        if r.status_code == 401:
            raise SystemExit("Groq rejected the API key (401). Check GROQ_API_KEY in .env.")
        r.raise_for_status()
        ids = [m["id"] for m in r.json().get("data", []) if not any(s in m["id"].lower() for s in SKIP)]
        ranked = []
        for p in PREFER:
            ranked += [i for i in ids if p in i.lower() and i not in ranked]
        _models = ranked + [i for i in ids if i not in ranked]
    return _models


def _call(model, system, user, max_tokens):
    """One model, up to 3 tries. Returns parsed dict, or (None, error_text)."""
    err = ""
    for _ in range(3):
        try:
            r = httpx.post(
                f"{BASE}/chat/completions",
                headers={"Authorization": f"Bearer {_key()}"},
                json={
                    "model": model,
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                    "temperature": 0.3,
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"},
                },
                timeout=60,
            )
        except httpx.HTTPError as exc:
            err = f"{type(exc).__name__}"
            time.sleep(2)
            continue
        if r.status_code == 401:
            raise SystemExit("Groq rejected the API key (401). Check GROQ_API_KEY in .env.")
        if r.status_code == 429:
            wait = float(r.headers.get("retry-after", 5))
            err = f"429 rate limit on {model}"
            if wait > 30:
                return None, err
            time.sleep(wait + 1)
            continue
        if r.status_code >= 500:
            err = f"{r.status_code} server error on {model}"
            time.sleep(2)
            continue
        if r.status_code >= 400:
            return None, f"{r.status_code} on {model}: {r.text[:150]}"
        try:
            return json.loads(r.json()["choices"][0]["message"]["content"]), ""
        except (ValueError, KeyError, IndexError):
            err = f"bad JSON from {model}"
    return None, err


def chat_json(system, user, max_tokens=1500):
    errors, tried = [], set()
    candidates = list(CONFIGURED)
    for phase in (0, 1):
        for model in candidates:
            if model in tried:
                continue
            tried.add(model)
            data, err = _call(model, system, user, max_tokens)
            if data is not None:
                return data
            errors.append(err)
        if phase == 0:  # configured models failed (or none set): ask Groq what is available
            candidates = available_models()[:4]
    raise RuntimeError("All Groq models failed: " + " | ".join(errors))