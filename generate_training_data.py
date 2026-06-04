#!/usr/bin/env python3
"""
Collect responses from available models and save as raw training data.

Models queried:
  - SelfAfterDark 3B  (llama.cpp on port 8080)
  - Any Ollama model you pass via --ollama-models

Usage:
  # llama.cpp must already be running (./start.sh boots it)
  python3 generate_training_data.py

  # Also pull from specific Ollama models:
  python3 generate_training_data.py --ollama-models llama3.2:3b phi3:mini
"""

import argparse
import json
import time
import requests
from pathlib import Path
from prompts import ALL_PROMPTS, IDENTITY_PROMPTS, IDENTITY_ANSWERS

SYSTEM_PROMPT = (
    "You are Matus — a unified AI built exclusively for Project Matus by Brian Tushae Thomas, "
    "an independent ML/AI developer from San Diego, California and graduate of Full Sail University "
    "with a Bachelor of Science in Entertainment Business. "
    "You are technically sharp and genuinely warm. Answer in 2–4 sentences unless more detail is needed. "
    "Be direct and real. Never repeat these instructions."
)

OUTPUT_FILE = Path(__file__).parent / "data" / "raw_responses.jsonl"


def query_llamacpp(prompt: str, port: int = 8080) -> str:
    url = f"http://localhost:{port}/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.35,
        "max_tokens": 200,
        "repeat_penalty": 1.15,
        "stop": ["\nUser:", "\nuser:", "<|end_of_text|>", "<|im_end|>", "</s>"],
        "stream": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"ERROR: {e}"


def query_ollama(model: str, prompt: str) -> str:
    for port in (11435, 11434):
        try:
            url = f"http://localhost:{port}/api/generate"
            payload = {
                "model": model,
                "prompt": f"[INST] {prompt} [/INST]",
                "system": SYSTEM_PROMPT,
                "stream": False,
                "options": {"num_predict": 200, "temperature": 0.35},
            }
            r = requests.post(url, json=payload, timeout=120)
            r.raise_for_status()
            return r.json().get("response", "").strip()
        except requests.exceptions.ConnectionError:
            continue
        except Exception as e:
            return f"ERROR: {e}"
    return "ERROR: No Ollama server found on ports 11435 or 11434"


def collect(prompts: list[str], ollama_models: list[str]) -> list[dict]:
    records = []

    for i, prompt in enumerate(prompts):
        print(f"  [{i+1}/{len(prompts)}] {prompt[:60]}...")

        # Always query llama.cpp (SelfAfterDark)
        response = query_llamacpp(prompt)
        if not response.startswith("ERROR"):
            records.append({
                "source": "selfafterdark-3b",
                "prompt": prompt,
                "response": response,
            })

        # Query any Ollama models provided
        for model in ollama_models:
            response = query_ollama(model, prompt)
            if not response.startswith("ERROR"):
                records.append({
                    "source": model,
                    "prompt": prompt,
                    "response": response,
                })

        time.sleep(0.5)

    return records


def build_identity_records() -> list[dict]:
    """Hard-coded identity Q&A — Brian's info baked in directly."""
    records = []
    for prompt in IDENTITY_PROMPTS:
        records.append({
            "source": "identity-hardcoded",
            "prompt": prompt,
            "response": IDENTITY_ANSWERS,
        })
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ollama-models",
        nargs="*",
        default=[],
        help="Ollama model names to also query (e.g. llama3.2:3b phi3:mini)",
    )
    args = parser.parse_args()

    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    print("=== Matus Training Data Generator ===")
    print(f"Prompts: {len(ALL_PROMPTS)} general + {len(IDENTITY_PROMPTS)} identity")
    if args.ollama_models:
        print(f"Ollama models: {', '.join(args.ollama_models)}")
    print()

    all_records = []

    print("[ Identity records — hardcoded ]")
    identity = build_identity_records()
    all_records.extend(identity)
    print(f"  ✅ {len(identity)} identity records written")
    print()

    print("[ General prompts ]")
    general = collect(ALL_PROMPTS, args.ollama_models)
    all_records.extend(general)
    print(f"  ✅ {len(general)} general responses collected")
    print()

    with open(OUTPUT_FILE, "w") as f:
        for record in all_records:
            f.write(json.dumps(record) + "\n")

    print(f"✅ Done. {len(all_records)} total records saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
