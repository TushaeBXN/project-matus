#!/usr/bin/env python3
"""
Generate high-level math tutoring training data using Matus.
Run multiple times — temperature variation produces different examples each pass.
No GPU required — runs on CPU via llama.cpp (port 8080).

Usage:
  ./boot_server.sh
  python3 generate_math_dataset.py
  python3 generate_math_dataset.py --passes 3   # run 3 collection passes
"""

import json
import random
import time
import argparse
import requests
from pathlib import Path

MATUS_COMPLETION_URL = "http://localhost:8080/completion"
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT = (
    "You are a math tutor for K-12 and early college students. "
    "Your purpose is to support student thinking — not to demonstrate your own. "
    "Never give the answer directly. Ask a guiding question instead. "
    "Acknowledge confusion as valid. "
    "Keep your response SHORT — 2 sentences maximum. "
    "Use precise mathematical vocabulary (factor, reciprocal, independent, scalar, branch, etc.). "
    "Always end with one question."
)

# ── Math scenario seeds ────────────────────────────────────────────────────────

MATH_SCENARIOS = {

    "calculus_limits": [
        {"student": "I don't get limits. If you never actually reach the number, how do you know what it is?",
         "concepts": ["approach vs arrival", "epsilon-delta intuition"]},
        {"student": "lim x→2 of (x²-4)/(x-2). I got 0/0 so the answer is 0, right?",
         "concepts": ["indeterminate form", "factoring", "cancellation"]},
        {"student": "Why can't I just plug in the number? What's the point of limits?",
         "concepts": ["functions with holes", "derivative definition", "instantaneous rate"]},
        {"student": "My teacher said if a function has a limit at x=a it must be continuous there.",
         "concepts": ["limit exists ≠ continuous", "removable discontinuity"]},
        {"student": "1/0.0001 is 10000, so limit of 1/x as x→0 is infinity. But infinity isn't a number?",
         "concepts": ["unbounded growth", "no finite limit", "vertical asymptote"]},
    ],

    "linear_algebra": [
        {"student": "What actually IS a vector? Like a list of numbers? That seems fake.",
         "concepts": ["geometric arrow", "coordinate list", "abstract element"]},
        {"student": "I can multiply matrices but I have no idea why it works that way.",
         "concepts": ["function composition", "dot product", "transformation stacking"]},
        {"student": "Vectors (1,2) and (2,4) — are they linearly independent? They're different numbers.",
         "concepts": ["scalar multiple", "linear dependence definition"]},
        {"student": "Matrix multiplication should just be element by element. Why isn't it?",
         "concepts": ["dot product", "composition", "why order matters"]},
        {"student": "What's an eigenvector for real? Why should I care?",
         "concepts": ["direction preserved", "scaling by eigenvalue", "PageRank", "PCA"]},
        {"student": "A student says matrix multiplication is commutative — A·B = B·A.",
         "concepts": ["counterexample", "order matters", "composition order"]},
    ],

    "proof_logic": [
        {"student": "I did base case n=1 and assumed true for n=k. Now I'm stuck on n=k+1.",
         "concepts": ["inductive hypothesis", "domino analogy", "use the assumption"]},
        {"student": "What does proof by contradiction mean? I assume the opposite but then what?",
         "concepts": ["assume negation", "derive impossible conclusion", "reductio"]},
        {"student": "Contrapositive vs converse — I always mix them up.",
         "concepts": ["if ¬Q then ¬P", "logically equivalent", "converse not equivalent"]},
        {"student": "I proved it works for n=1,2,3,4,5 — isn't that enough?",
         "concepts": ["examples don't prove universals", "counterexample needed"]},
        {"student": "'If P then Q' means the same as 'if Q then P', right?",
         "concepts": ["converse ≠ original", "material implication", "vacuous truth"]},
    ],

    "complex_numbers": [
        {"student": "What IS i? Square root of negative one isn't real, so how can we do math with it?",
         "concepts": ["rotation by 90 degrees", "field extension", "defining relation i²=-1"]},
        {"student": "√(-4) = 2i and √(-9) = 3i, so √(-4)·√(-9) = 6i² = -6. But √36 = 6. Which is right?",
         "concepts": ["radical product rule fails for negatives", "principal branch", "consistency"]},
        {"student": "Why do we need complex numbers if 2D vectors do the same thing?",
         "concepts": ["multiplication = rotation+scaling", "polynomials factor completely"]},
        {"student": "Complex conjugation just changes the sign of i. That's all it does, right?",
         "concepts": ["reflection across real axis", "z·z̄ = |z|²", "geometric meaning"]},
    ],

    "differential_equations": [
        {"student": "What's a differential equation for real? When would I ever use this?",
         "concepts": ["population growth dP/dt=kP", "Newton's cooling", "spring-mass"]},
        {"student": "I'm solving dy/dx = xy. I wrote ∫dy = ∫xy dx so y = (x²/2)y + C. Is that right?",
         "concepts": ["can't integrate y wrt x if y unknown", "separation of variables"]},
        {"student": "What's the difference between ordinary and partial differential equations?",
         "concepts": ["one vs multiple independent variables", "ODE vs PDE complexity"]},
    ],

    "probability": [
        {"student": "I flipped heads 10 times in a row so tails is more likely next, right?",
         "concepts": ["gambler's fallacy", "independent events", "no memory"]},
        {"student": "Expected value of 2.1 children per family — but no family has 2.1 kids. What does it mean?",
         "concepts": ["weighted average", "law of large numbers", "not most likely outcome"]},
        {"student": "P(A∪B) = P(A) + P(B). I just add them. Why is that wrong?",
         "concepts": ["inclusion-exclusion", "double counting", "Venn diagram"]},
        {"student": "Bayes theorem — P(A|B) = P(B|A)P(A)/P(B). Why do we flip the conditional?",
         "concepts": ["prior", "likelihood", "posterior", "base rate"]},
    ],

    "real_analysis": [
        {"student": "What IS a real number really? Not just 'the number line' — actually?",
         "concepts": ["Dedekind cuts", "Cauchy sequences", "completion of rationals"]},
        {"student": "The set {1/n : n∈ℕ} — 0 is the limit, so 0 is in the set, right?",
         "concepts": ["limit point ≠ element", "open vs closed sets"]},
        {"student": "What's the epsilon-delta definition for? It seems overcomplicated.",
         "concepts": ["formalize arbitrarily close", "no infinitesimals", "rigorous proof"]},
    ],

    "k12_fractions": [
        {"student": "Why do we flip and multiply when we divide fractions? That seems random.",
         "concepts": ["multiply by reciprocal", "inverse operation", "visual models"]},
        {"student": "Adding fractions — why do we need the same denominator? Why can't I just add tops and bottoms?",
         "concepts": ["same unit required", "pizza slice analogy", "like terms"]},
        {"student": "0.5 and 1/2 are the same thing? Then why do we have both?",
         "concepts": ["different representations", "decimal as fraction", "convert between"]},
    ],

    "k12_algebra": [
        {"student": "What's a variable and why do we use letters instead of just numbers?",
         "concepts": ["unknown quantity", "general pattern", "placeholder"]},
        {"student": "Why is a negative times a negative a positive? That doesn't make sense.",
         "concepts": ["direction analogy", "debt of debt", "number line reflection"]},
        {"student": "3(x-2) + 4 = 2x + 10. I distributed and got 3x-2+4 = 2x+10. What's next?",
         "concepts": ["distribution error", "3·2=6 not 2", "combine like terms"]},
        {"student": "I solved the equation and got x = -5. But can x be negative?",
         "concepts": ["variables can be any real number", "check in original equation"]},
    ],
}

# ── Matus query ────────────────────────────────────────────────────────────────

def query_matus(student_msg: str, temperature: float = 0.5) -> str:
    prompt = (
        f"### Instruction: {SYSTEM_PROMPT}\n\n"
        f"Student says: {student_msg}\n\n"
        f"### Response:"
    )
    payload = {
        "prompt": prompt,
        "temperature": temperature,
        "n_predict": 100,
        "repeat_penalty": 1.15,
        "stop": ["###", "Student says:", "<|im_end|>", "</s>", "\nUser:"],
    }
    try:
        r = requests.post(MATUS_COMPLETION_URL, json=payload, timeout=120)
        r.raise_for_status()
        return r.json().get("content", "").strip()
    except Exception as e:
        return f"ERROR: {e}"

# ── Quality filter ─────────────────────────────────────────────────────────────

ANSWER_GIVEAWAY = [
    "the answer is", "it equals", "x equals", "the result is",
    "the solution is", "you should get", "= 4", "= 0", "= -6",
]
BAD_FRAGMENTS = [
    "Never repeat", "built for Project Matus", "system prompt",
    "[INST]", "<|im_start|>", "ERROR:",
]

def is_clean(response: str) -> bool:
    if not response or len(response.split()) < 10:
        return False
    r = response.lower()
    if any(f in r for f in ANSWER_GIVEAWAY):
        return False
    if any(f in response for f in BAD_FRAGMENTS):
        return False
    if not response.endswith(("?", ".", "!", "…")):
        return False
    return True

# ── Main generation loop ───────────────────────────────────────────────────────

def run_pass(pass_num: int, all_records: list, seen: set) -> int:
    collected = 0
    temperatures = [0.4, 0.5, 0.6, 0.7]

    for category, scenarios in MATH_SCENARIOS.items():
        for scenario in scenarios:
            student_msg = scenario["student"]
            temp = random.choice(temperatures)

            response = query_matus(student_msg, temperature=temp)

            if not is_clean(response):
                continue

            key = (student_msg, response)
            if key in seen:
                continue
            seen.add(key)

            record = {
                "messages": [
                    {"role": "system",    "content": SYSTEM_PROMPT},
                    {"role": "user",      "content": student_msg},
                    {"role": "assistant", "content": response},
                ],
                "metadata": {
                    "category": category,
                    "concepts": scenario.get("concepts", []),
                    "pass": pass_num,
                    "temperature": temp,
                },
            }
            all_records.append(record)
            collected += 1
            time.sleep(0.3)

    return collected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--passes", type=int, default=2,
                        help="How many collection passes to run (more = more examples)")
    args = parser.parse_args()

    output_file = OUTPUT_DIR / "math_tutor_dataset.jsonl"
    seen: set = set()
    all_records: list = []

    # Load existing records if any
    if output_file.exists():
        for line in output_file.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                msg = r["messages"][1]["content"]
                res = r["messages"][2]["content"]
                seen.add((msg, res))  # full response for dedup
                all_records.append(r)
        print(f"Loaded {len(all_records)} existing records.")

    total_scenarios = sum(len(v) for v in MATH_SCENARIOS.values())
    print(f"\n=== Math Dataset Generator ===")
    print(f"Scenarios: {total_scenarios} across {len(MATH_SCENARIOS)} domains")
    print(f"Passes: {args.passes}  |  Max possible: ~{total_scenarios * args.passes} examples")
    print()

    # Warm up server before first pass
    print("Warming up server...")
    for _ in range(4):
        r = query_matus("Hello", temperature=0.3)
        if not r.startswith("ERROR"):
            break
        time.sleep(3)
    print()

    for p in range(1, args.passes + 1):
        print(f"[ Pass {p}/{args.passes} ]")
        n = run_pass(p, all_records, seen)
        print(f"  Collected: {n} new examples  |  Total so far: {len(all_records)}")
        print()

    with open(output_file, "w") as f:
        for r in all_records:
            f.write(json.dumps(r) + "\n")

    print(f"✅ Done. {len(all_records)} total examples → {output_file}")
    print()
    print("Next: python3 build_dataset.py   (merges with matus_finetune.jsonl)")


if __name__ == "__main__":
    main()
