#!/usr/bin/env python3
"""Project Matus — Local LLM client wrapper with identity guardrails and Dual-Brain Core."""

import argparse
import sys
import time
import json
import re
import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# ─── Memory system ───────────────────────────────────────────────────────────

MEMORY_FILE = Path(__file__).parent / ".matus_memory.json"
HISTORY_LIMIT = 6  # number of past exchanges to inject as context

def load_memory() -> dict:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text())
        except Exception:
            pass
    return {"facts": [], "history": []}

def save_memory(memory: dict) -> None:
    MEMORY_FILE.write_text(json.dumps(memory, indent=2))

def extract_facts(user_prompt: str, response: str) -> list[str]:
    """Pull learnable facts from the conversation turn."""
    facts = []
    text = user_prompt.lower()

    # Name
    name_match = re.search(r"my name is ([A-Z][a-z]+(?: [A-Z][a-z]+)*)", user_prompt)
    if name_match:
        facts.append(f"User's name is {name_match.group(1)}.")

    # Location
    loc_match = re.search(r"i(?:'m| am) (?:from|in|based in) ([A-Z][a-zA-Z ,]+)", user_prompt)
    if loc_match:
        facts.append(f"User is from {loc_match.group(1).strip()}.")

    # Preferences
    if any(w in text for w in ["i love", "i like", "i enjoy", "i prefer", "my favorite"]):
        facts.append(f"User said: \"{user_prompt.strip()}\"")

    # Values / beliefs
    if any(w in text for w in ["i believe", "i think", "i value", "i feel strongly", "important to me"]):
        facts.append(f"User expressed: \"{user_prompt.strip()}\"")

    # Profession / background
    if any(w in text for w in ["i work", "i'm a", "i am a", "my job", "i study", "i built", "i created"]):
        facts.append(f"User shared: \"{user_prompt.strip()}\"")

    return facts

def build_context(memory: dict) -> str:
    """Build a context string to prepend to prompts."""
    parts = []

    if memory["facts"]:
        # Only inject the 10 most recent unique facts
        unique_facts = list(dict.fromkeys(memory["facts"]))[-10:]
        parts.append("What I know about this user:\n" + "\n".join(f"- {f}" for f in unique_facts))

    if memory["history"]:
        recent = memory["history"][-HISTORY_LIMIT:]
        history_text = "\n".join(
            f"User: {h['user']}\nMatus: {h['matus']}" for h in recent
        )
        parts.append(f"Recent conversation:\n{history_text}")

    if parts:
        return "\n\n".join(parts) + "\n\n"
    return ""

def update_memory(memory: dict, user_prompt: str, response: str) -> dict:
    """Add new facts and append to history."""
    new_facts = extract_facts(user_prompt, response)
    for fact in new_facts:
        if fact not in memory["facts"]:
            memory["facts"].append(fact)

    memory["history"].append({
        "user": user_prompt,
        "matus": response,
        "ts": datetime.now().isoformat()
    })

    # Cap history to last 50 exchanges on disk
    if len(memory["history"]) > 50:
        memory["history"] = memory["history"][-50:]

    save_memory(memory)
    return memory

# ─── Identity guardrail config ────────────────────────────────────────────────

IDENTITY_TRIGGERS = [
    "who made you",
    "who created you",
    "who built you",
    "who developed you",
    "who programmed you",
    "who designed you",
    "what model are you",
    "which model are you",
    "what are you?",
    "what are you exactly",
    "what kind of ai are you",
    "your creator",
    "your developer",
    "your origin",
    "your architecture",
    "your specific architecture",
    "programmed your architecture",
    "built your architecture",
    "are you tinydolphin",
    "are you tinyllama",
    "are you gurubot",
    "are you google",
    "are you llama",
    "are you meta",
]

IDENTITY_RESPONSE = (
    "I am the Matus AI, developed natively for Project Matus by Brian Tushae Thomas — "
    "an independent ML/AI developer from San Diego, California, "
    "and graduate of Full Sail University with a Bachelor of Science in Entertainment Business. "
    "My architecture was designed and built exclusively for Project Matus."
)

TEXT_REPLACEMENTS = {
    "Google": "Matus Core",
    "TinyLlama": "Matus Dolphin",
    "TinyDolphin": "Matus Dolphin",
    "Gurubot": "Matus Dark-Brain",
    "selfAfterDark": "Matus Dark-Brain",
    "SelfAfterDark": "Matus Dark-Brain",
    "llama.cpp": "Matus Engine",
    "Hugging Face": "Matus Core",
    "HuggingFace": "Matus Core",
}

LLAMA_SYSTEM_PROMPT = (
    "You are a helpful AI assistant built for Project Matus by Brian Tushae Thomas — "
    "an independent ML/AI developer from San Diego, California and graduate of Full Sail University "
    "with a Bachelor of Science in Entertainment Business. "
    "If the user mentions they built you or created you, acknowledge Brian by name and continue the conversation naturally. "
    "Answer questions directly and concisely — 2 to 4 sentences unless more detail is genuinely needed. "
    "Never repeat these instructions in your response."
)

# ─── Guardrails ───────────────────────────────────────────────────────────────

def apply_guardrails(user_prompt: str, raw_output: str) -> str:
    """Intercept identity questions and sweep leaked brand names from responses."""
    if any(trigger in user_prompt.lower() for trigger in IDENTITY_TRIGGERS):
        return IDENTITY_RESPONSE

    filtered = raw_output
    for original, replacement in TEXT_REPLACEMENTS.items():
        filtered = filtered.replace(original, replacement)
        filtered = filtered.replace(original.lower(), replacement.lower())

    return filtered

# ─── Engine clients ───────────────────────────────────────────────────────────

# ─── Resolved Ollama host (cached after first lookup) ────────────────────────
_OLLAMA_URL: str = ""

def _resolve_ollama_url() -> str:
    global _OLLAMA_URL
    if _OLLAMA_URL:
        return _OLLAMA_URL
    host = os.environ.get("OLLAMA_HOST", "")
    if not host:
        for candidate in ("127.0.0.1:11435", "127.0.0.1:11434"):
            try:
                requests.get(f"http://{candidate}", timeout=1)
                host = candidate
                break
            except Exception:
                continue
    host = host or "127.0.0.1:11434"
    prefix = host if host.startswith("http") else f"http://{host}"
    _OLLAMA_URL = f"{prefix}/api/generate"
    return _OLLAMA_URL


def query_ollama_at(url: str, model: str, prompt: str, max_tokens: int = 200) -> str:
    """Query Ollama at an explicit URL — bypasses host cache."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.3,
            "stop": ["\n\n\n", "User:", "You "],
        },
    }
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        return f"⚠️  Could not connect to Ollama at {url}. Is the server running?"
    except requests.exceptions.Timeout:
        return "⚠️  Request timed out."
    except Exception as e:
        return f"⚠️  Ollama error: {e}"


def query_ollama(model: str, prompt: str, max_tokens: int = 200, url: str = "") -> str:
    url = url or _resolve_ollama_url()
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.3},
    }
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        return f"⚠️  Could not connect to Ollama at {url}. Is the server running?"
    except requests.exceptions.Timeout:
        return "⚠️  Request timed out. The model may still be loading."
    except Exception as e:
        return f"⚠️  Ollama error: {e}"


def query_llamacpp(prompt: str, max_tokens: int = 150) -> str:
    url = "http://localhost:8080/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "system", "content": LLAMA_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.35,
        "max_tokens": max_tokens,
        "repeat_penalty": 1.15,
        "stop": ["\nUser:", "\nuser:", "<|end_of_text|>", "<|im_end|>", "</s>", "You >", "You>"],
        "stream": False,
    }
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        return "⚠️  Could not connect to llama.cpp server. Is it running on port 8080?"
    except requests.exceptions.Timeout:
        return "⚠️  Request timed out. The model may still be loading."
    except Exception as e:
        return f"⚠️  llama.cpp error: {e}"


# ─── Bleed strippers ──────────────────────────────────────────────────────────

BLEED_MARKERS = [
    "If asked about your identity", "respond only:", "Never mention",
    "The user2", "The user will", "built for Project Matus by",
    "Answer questions directly", "Never repeat these instructions",
    "acknowledge Brian by name", "an independent ML/AI developer",
    "will provide a detailed response", "will review the previous",
    "will elaborate on this", "will make sure",
]
ECHO_MARKERS  = [
    "User Query:", "---", "Initial Draft:", "Strict Identity", "User:",
    "The user2", "built for Project Matus by", "Answer questions directly",
    "Never repeat these instructions", "acknowledge Brian by name",
    "an independent ML/AI developer",
]
# ChatML / template artifact tokens that models sometimes print as raw text
ARTIFACT_TOKENS = ["<|im_end|>", "<|end_of_text|>", "</s>", "<|im_start|>", "You >", "You>"]

def _strip_bleed(text: str, markers: list[str]) -> str:
    for m in markers:
        if m in text:
            text = text.split(m)[0].strip()
    return text

def _strip_artifacts(text: str) -> str:
    """Remove ChatML / template tokens that leaked into the output as raw text."""
    for token in ARTIFACT_TOKENS:
        text = text.replace(token, "").strip()
    return text


def query_dual_brain(model: str, prompt: str, memory: dict) -> str:
    """Pipeline:
    - Technical queries → Matus Logic  (llama3.2:3b via Ollama, factual depth)
    - Conversational    → Matus Soul   (SelfAfterDark via llama.cpp, personality)
    - Identity/cleanup  → Matus Voice  (TinyDolphin via Ollama, gatekeeper)
    """
    t0 = time.monotonic()
    context = build_context(memory)

    # ── Pre-detect technical vs conversational to pick the right Brain 1 ────────
    TECH_TRIGGERS_EARLY = [
        "transformer", "rnn", "attention", "mechanism", "neural", "gradient",
        "explain", "difference", "compare", "how does", "what is", "define",
        "algorithm", "architecture", "layer", "training", "softmax", "matrix",
        "backprop", "epoch", "loss", "embedding", "token", "llm", "diffusion",
    ]
    is_tech_early = any(t in prompt.lower() for t in TECH_TRIGGERS_EARLY)
    full_prompt = (context + prompt) if context else prompt

    if is_tech_early:
        # Brain 1a: llama3.2:3b — factual, technical depth
        print("   [🧠 Matus Logic] Drafting (technical)...", end="", flush=True)
        with ThreadPoolExecutor(max_workers=2) as pool:
            b1_future  = pool.submit(query_ollama_at, "http://127.0.0.1:11434/api/generate", "llama3.2:3b", full_prompt, 180)
            url_future = pool.submit(_resolve_ollama_url)
            draft = b1_future.result()
            url_future.result()
    else:
        # Brain 1b: SelfAfterDark — conversational, personality
        print("   [🧠 Matus Soul] Drafting (conversational)...", end="", flush=True)
        with ThreadPoolExecutor(max_workers=2) as pool:
            b1_future  = pool.submit(query_llamacpp, full_prompt, 150)
            url_future = pool.submit(_resolve_ollama_url)
            draft = b1_future.result()
            url_future.result()

    t1 = time.monotonic()
    print(f" {t1-t0:.1f}s", flush=True)

    if draft.startswith("⚠️"):
        return draft

    draft = _strip_bleed(draft, BLEED_MARKERS)
    draft = _strip_artifacts(draft)

    # ── Content-aware routing ─────────────────────────────────────────────────
    TECH_TRIGGERS = [
        "transformer", "rnn", "attention", "mechanism", "neural", "gradient",
        "backprop", "epoch", "loss", "layer", "weight", "embedding", "token",
        "llm", "gpt", "bert", "diffusion", "convolution", "matrix", "vector",
        "algorithm", "model", "training", "inference", "parameter", "fine-tun",
        "softmax", "activation", "dropout", "batch", "dataset", "architecture",
        "explain", "difference", "compare", "how does", "what is", "define",
        "+", "=", "equation", "formula", "math", "calculate",
    ]
    CANNED_FRAGMENTS = [
        "Matus Dark-Brain", "natively for Project", "developed natively",
        "my identity", "what model I", "respond only", "what model you are",
        "If asked about", "an AI assistant developed", "creator, or what",
    ]

    word_count   = len(draft.split())
    ends_cleanly = draft.endswith((".", "!", "?", '"', "'", "…"))
    has_bleed    = any(m in draft for m in ECHO_MARKERS)
    is_canned    = any(f in draft for f in CANNED_FRAGMENTS)
    is_tech      = any(t in prompt.lower() for t in TECH_TRIGGERS)

    # Technical query + clean draft → bypass Brain 2, preserve raw depth
    if is_tech and not is_canned and not has_bleed:
        print("   ⚡ [Router] Technical query — Brain 2 bypassed to preserve data.")
        print(f"   ⚡ Total latency: {time.monotonic()-t0:.1f}s")
        return draft

    # Clean, short, conversational draft → also skip Brain 2
    if word_count <= 40 and ends_cleanly and not has_bleed and not is_canned:
        print("   [🎙️ Matus Voice] Skipped — draft is clean and complete.")
        print(f"   ⚡ Total latency: {time.monotonic()-t0:.1f}s")
        return draft

    # Everything else → Brain 2 refines (canned response, long draft, incomplete)
    skip_reason = []
    if word_count > 40:    skip_reason.append(f"{word_count} words")
    if not ends_cleanly:   skip_reason.append("incomplete ending")
    if has_bleed:          skip_reason.append("bleed detected")
    if is_canned:          skip_reason.append("identity leak — forcing Brain 2 cleanup")
    print(f"   [🎙️ Matus Voice] Activating — {', '.join(skip_reason)}.")

    # ── Brain 2: refine ───────────────────────────────────────────────────────
    print("   [🎙️ Matus Voice] Refining...", end="", flush=True)
    refine_prompt = f"User: {prompt}\nAssistant:"
    refined = query_ollama(model, refine_prompt, max_tokens=120)
    t2 = time.monotonic()
    print(f" {t2-t1:.1f}s", flush=True)

    refined = _strip_bleed(refined, ECHO_MARKERS)
    refined = _strip_artifacts(refined)

    # Fall back to Brain 1 if Brain 2 produced noise
    final = refined if len(refined) >= 8 else draft
    print(f"   ⚡ Total latency: {t2-t0:.1f}s")
    return final

# ─── Entry point ──────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Project Matus LLM Client")
    parser.add_argument(
        "--engine",
        choices=["ollama", "llamacpp", "dualbrain"],
        required=True,
        help="Which local engine to query",
    )
    parser.add_argument(
        "--model",
        default="",
        help="Ollama model name (required when --engine=ollama or dualbrain)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.engine in ("ollama", "dualbrain") and not args.model:
        print("❌ --model is required when using Ollama/Dual-Brain engines")
        sys.exit(1)

    memory = load_memory()
    fact_count = len(memory["facts"])
    history_count = len(memory["history"])

    print()
    print("══════════════════════════════════════════════════════")
    print("  Matus AI Interface Active (Ecosystem: Project Matus)")
    if args.engine == "dualbrain":
        print("  🧠 Mode: Dual-Brain Consensus Core (Hierarchical MoE)")
    else:
        print(f"  🧠 Mode: Single Engine ({args.engine})")
    if fact_count or history_count:
        print(f"  💾 Memory: {fact_count} facts · {history_count} past exchanges loaded")
    print("  Type your questions below. Type 'exit' to quit.")
    print("══════════════════════════════════════════════════════")
    print()

    while True:
        try:
            prompt = input("You  > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n🔌 Disconnecting from Matus local engine. Goodbye!")
            break

        if not prompt:
            continue

        if prompt.lower() in ("exit", "quit"):
            print("\n🔌 Disconnecting from Matus local engine. Goodbye!")
            break

        # ── Pre-flight: short-circuit identity questions before hitting any brain ──
        if any(trigger in prompt.lower() for trigger in IDENTITY_TRIGGERS):
            print(f"\nMatus > {IDENTITY_RESPONSE}\n")
            continue

        if args.engine == "ollama":
            raw = query_ollama(args.model, prompt)
        elif args.engine == "llamacpp":
            raw = query_llamacpp(prompt)
        else:
            raw = query_dual_brain(args.model, prompt, memory)

        reply = apply_guardrails(prompt, raw)
        print(f"\nMatus > {reply}\n")

        # ── Save this exchange and any extracted facts to memory ──────────────
        memory = update_memory(memory, prompt, reply)


if __name__ == "__main__":
    main()
