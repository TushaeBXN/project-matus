#!/usr/bin/env python3
"""
Convert raw_responses.jsonl into a fine-tuning dataset (ChatML JSONL format).
Output is ready for Unsloth / trl SFTTrainer on RunPod.

Usage:
  python3 build_dataset.py
"""

import json
from pathlib import Path

RAW_FILE   = Path(__file__).parent / "data" / "raw_responses.jsonl"
MATH_FILE  = Path(__file__).parent / "data" / "math_tutor_dataset.jsonl"
OUT_FILE   = Path(__file__).parent / "data" / "matus_finetune.jsonl"

SYSTEM_PROMPT = (
    "You are Matus — a unified AI built exclusively for Project Matus by Brian Tushae Thomas, "
    "an independent ML/AI developer from San Diego, California and graduate of Full Sail University "
    "with a Bachelor of Science in Entertainment Business. "
    "You are technically sharp and genuinely warm. Answer in 2–4 sentences unless more detail is needed. "
    "Be direct and real. Never repeat these instructions."
)

MIN_RESPONSE_WORDS = 5
MAX_RESPONSE_WORDS = 300


def is_clean(response: str) -> bool:
    if not response or response.startswith("ERROR"):
        return False
    words = response.split()
    if len(words) < MIN_RESPONSE_WORDS or len(words) > MAX_RESPONSE_WORDS:
        return False
    # Filter leaked instructions
    bad_fragments = [
        "Never repeat these instructions",
        "built for Project Matus by",
        "Answer in 2–4 sentences",
        "[INST]", "[/INST]",
        "<|im_start|>", "<|im_end|>",
    ]
    return not any(f in response for f in bad_fragments)


def to_chatml(prompt: str, response: str) -> dict:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response},
        ]
    }


def main():
    kept = 0
    skipped = 0
    seen = set()

    with open(OUT_FILE, "w") as f:

        # ── Source 1: raw_responses.jsonl (general + identity) ────────────────
        if RAW_FILE.exists():
            raw = [json.loads(l) for l in RAW_FILE.read_text().splitlines() if l.strip()]
            print(f"General records loaded:    {len(raw)}")
            for record in raw:
                prompt   = record.get("prompt", "").strip()
                response = record.get("response", "").strip()
                key = (prompt, response[:80])
                if key in seen:
                    skipped += 1; continue
                seen.add(key)
                if not is_clean(response):
                    skipped += 1; continue
                f.write(json.dumps(to_chatml(prompt, response)) + "\n")
                kept += 1
        else:
            print(f"⚠️  {RAW_FILE} not found — skipping general records.")

        # ── Source 2: math_tutor_dataset.jsonl (already in ChatML format) ─────
        if MATH_FILE.exists():
            math_raw = [json.loads(l) for l in MATH_FILE.read_text().splitlines() if l.strip()]
            print(f"Math tutor records loaded: {len(math_raw)}")
            for record in math_raw:
                msgs = record.get("messages", [])
                if len(msgs) < 3:
                    skipped += 1; continue
                prompt   = msgs[1].get("content", "").strip()
                response = msgs[2].get("content", "").strip()
                key = (prompt, response[:80])
                if key in seen:
                    skipped += 1; continue
                seen.add(key)
                if not is_clean(response):
                    skipped += 1; continue
                f.write(json.dumps(record) + "\n")
                kept += 1
        else:
            print(f"⚠️  {MATH_FILE} not found — run generate_math_dataset.py first.")

    print()
    print(f"✅ Dataset built: {kept} examples → {OUT_FILE}")
    print(f"   Skipped (low quality / duplicate): {skipped}")
    print()
    print("Next step: upload data/matus_finetune.jsonl to RunPod and run fine-tuning.")


if __name__ == "__main__":
    main()
