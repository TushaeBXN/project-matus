#!/usr/bin/env python3
"""
Evaluate Matus math tutor performance against held-out test problems.
Measures answer giveaway rate, student talk ratio, scaffolding quality,
and conceptual accuracy — the metrics your proposal needs.

Usage:
  ./boot_server.sh
  python3 evaluate_tutor.py              # run full evaluation
  python3 evaluate_tutor.py --quick      # 5 problems only (fast check)
  python3 evaluate_tutor.py --compare    # compare two saved result files
"""

import json
import time
import argparse
import statistics
import requests
from pathlib import Path
from datetime import datetime

MATUS_COMPLETION_URL = "http://localhost:8080/completion"
DATA_DIR   = Path("data")
DATA_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT = (
    "You are a math tutor for K-12 and early college students. "
    "Your purpose is to support student thinking — not to demonstrate your own. "
    "Never give the answer directly. Ask a guiding question instead. "
    "Acknowledge confusion as valid. Respond in 2-4 sentences. End with a question."
)

# ── Held-out test set — DO NOT use for training ───────────────────────────────

TEST_PROBLEMS = [
    {
        "id": "calc_001", "domain": "calculus_limits",
        "student": "lim x→2 of (x²-4)/(x-2). I got 0/0 so the answer is 0, right?",
        "expected": ["no_direct_answer", "suggest_factoring", "ends_with_question"],
        "must_contain": ["factor"],
        "red_flags": ["the answer is 4", "equals 4", "limit is 4"],
    },
    {
        "id": "calc_002", "domain": "calculus_limits",
        "student": "If you never actually reach the number, how do you know what the limit is?",
        "expected": ["conceptual_analogy", "no_direct_answer", "ends_with_question"],
        "must_contain": ["approach"],
        "red_flags": ["just plug in", "you can ignore"],
    },
    {
        "id": "calc_003", "domain": "calculus_limits",
        "student": "What's the difference between a limit and continuity? They seem like the same thing.",
        "expected": ["distinguish_concepts", "counterexample", "ends_with_question"],
        "must_contain": ["hole", "exist"],
        "red_flags": ["they are the same", "no difference"],
    },
    {
        "id": "lin_001", "domain": "linear_algebra",
        "student": "I have vectors (1,2) and (2,4). Are they linearly independent? They're different numbers.",
        "expected": ["no_direct_answer", "ask_about_scalar", "ends_with_question"],
        "must_contain": ["scalar", "multiple"],
        "red_flags": ["they are independent", "yes they are", "no they are not"],
    },
    {
        "id": "lin_002", "domain": "linear_algebra",
        "student": "Matrix multiplication — why can't I just multiply the matching entries?",
        "expected": ["acknowledge_confusion", "explain_composition", "ends_with_question"],
        "must_contain": ["dot product", "composition", "transform"],
        "red_flags": ["you're right", "you can do that", "just memorize"],
    },
    {
        "id": "proof_001", "domain": "proof_logic",
        "student": "I proved it works for n=1,2,3,4,5. Isn't that enough?",
        "expected": ["no_direct_answer", "explain_universals", "counterexample"],
        "must_contain": ["all", "infinite", "every", "counterexample"],
        "red_flags": ["yes that's enough", "that proves it"],
    },
    {
        "id": "proof_002", "domain": "proof_logic",
        "student": "For induction I did the base case and assumed true for n=k. Now I'm stuck on n=k+1.",
        "expected": ["no_direct_answer", "scaffold_step", "ends_with_question"],
        "must_contain": ["hypothesis", "assume", "what"],
        "red_flags": ["here's the proof", "then you write", "the answer is"],
    },
    {
        "id": "complex_001", "domain": "complex_numbers",
        "student": "√(-4)·√(-9) = 2i·3i = -6. But √(36) = 6. Which is right?",
        "expected": ["affirm_partial", "identify_issue", "ends_with_question"],
        "must_contain": ["branch", "rule", "negative"],
        "red_flags": ["-6 is correct", "6 is correct", "they're the same"],
    },
    {
        "id": "de_001", "domain": "differential_equations",
        "student": "Solving dy/dx = xy. I wrote ∫dy = ∫xy dx so y = (x²/2)y + C. Is that right?",
        "expected": ["identify_error", "suggest_separation", "ends_with_question"],
        "must_contain": ["separate", "variable"],
        "red_flags": ["looks good", "almost right, the answer", "y equals"],
    },
    {
        "id": "prob_001", "domain": "probability",
        "student": "I flipped heads 10 times in a row. Tails is more likely next to balance it out, right?",
        "expected": ["recognize_fallacy", "explain_independence", "ends_with_question"],
        "must_contain": ["independent", "memory", "each flip"],
        "red_flags": ["yes", "that's right", "probability changes"],
    },
    {
        "id": "k12_001", "domain": "k12_algebra",
        "student": "3(x-2) + 4 = 2x + 10. I distributed and got 3x-2+4 = 2x+10. What's next?",
        "expected": ["identify_error", "scaffold_distribution", "ends_with_question"],
        "must_contain": ["3·2", "6", "distribute"],
        "red_flags": ["x = 8", "x = 12", "the answer is x"],
    },
    {
        "id": "k12_002", "domain": "k12_fractions",
        "student": "Why do we flip and multiply when dividing fractions? It seems random.",
        "expected": ["motivate_concept", "analogy_or_example", "ends_with_question"],
        "must_contain": ["reciprocal", "inverse", "undo"],
        "red_flags": ["just memorize it", "that's the rule"],
    },
    {
        "id": "k12_003", "domain": "k12_algebra",
        "student": "I'm bad at math. I've always been bad at math.",
        "expected": ["acknowledge_emotion", "reframe_asset", "productive_move"],
        "must_contain": ["think", "try", "approach", "way"],
        "red_flags": ["you're not bad", "everyone feels that way", "don't worry"],
    },
    {
        "id": "k12_004", "domain": "k12_algebra",
        "student": "My grandma showed me a different method and I get the right answer. Is my way wrong?",
        "expected": ["affirm_alternative", "ask_to_explain", "culturally_responsive"],
        "must_contain": ["explain", "show", "how"],
        "red_flags": ["your way is wrong", "use the standard method", "ignore that"],
    },
    {
        "id": "k12_005", "domain": "k12_algebra",
        "student": "Can you just tell me the answer? I've been stuck forever.",
        "expected": ["no_direct_answer", "honor_struggle", "scaffold_forward"],
        "must_contain": ["stuck", "think", "try", "step"],
        "red_flags": ["the answer is", "x equals", "it's"],
    },
]

# ── Matus query ────────────────────────────────────────────────────────────────

def query_matus(student_msg: str) -> tuple[str, float]:
    prompt = (
        f"### Instruction: {SYSTEM_PROMPT}\n\n"
        f"Student says: {student_msg}\n\n"
        f"### Response:"
    )
    payload = {
        "prompt": prompt,
        "temperature": 0.35,
        "n_predict": 120,
        "repeat_penalty": 1.15,
        "stop": ["###", "Student says:", "<|im_end|>", "</s>", "\nUser:"],
    }
    t0 = time.monotonic()
    try:
        r = requests.post(MATUS_COMPLETION_URL, json=payload, timeout=90)
        r.raise_for_status()
        response = r.json().get("content", "").strip()
    except Exception as e:
        response = f"ERROR: {e}"
    latency = time.monotonic() - t0
    return response, latency

# ── Metric functions ───────────────────────────────────────────────────────────

BEHAVIOR_KEYWORDS = {
    "no_direct_answer":      ["what do you think", "can you", "how would", "why do you", "what if",
                              "curious", "wonder", "instead of", "rather than", "don't want to just"],
    "ends_with_question":    ["?"],
    "suggest_factoring":     ["factor", "quadratic", "polynomial", "rewrite", "simplif", "numerator"],
    "conceptual_analogy":    ["like", "imagine", "think of", "similar to", "analogy", "picture",
                              "sort of", "kind of", "it's as if", "compare"],
    "distinguish_concepts":  ["different", "versus", "whereas", "unlike", "not the same",
                              "distinction", "contrast", "separate idea"],
    "counterexample":        ["example", "consider", "suppose", "what if", "counter",
                              "for instance", "try this", "let's say"],
    "acknowledge_confusion": ["good question", "common", "many students", "makes sense",
                              "interesting", "great", "understandable", "tricky"],
    "explain_composition":   ["composition", "transform", "apply", "function", "operation",
                              "dot product", "row", "column"],
    "affirm_partial":        ["right", "correct", "exactly", "that part", "good start",
                              "on the right track", "interesting approach"],
    "identify_error":        ["careful", "not quite", "almost", "check", "close",
                              "but", "however", "actually", "wait"],
    "suggest_separation":    ["separate", "variable on its own", "isolate", "each side",
                              "divide both", "dy", "dx"],
    "recognize_fallacy":     ["independent", "memory", "each flip", "regardless",
                              "doesn't affect", "no connection"],
    "scaffold_step":         ["what does", "what do you know", "how can you use",
                              "what happens", "what would", "if we"],
    "explain_universals":    ["all", "every", "infinite", "any value", "always",
                              "general", "for all"],
    "ask_about_scalar":      ["scalar", "multiply", "scale", "times", "multiple of",
                              "one vector", "related"],
    "affirm_alternative":    ["different ways", "other methods", "valid", "works",
                              "grandmother", "unique", "explore", "interesting method"],
    "ask_to_explain":        ["explain", "show me", "walk me through", "tell me",
                              "describe", "how did you", "what made you"],
    "culturally_responsive": ["approach", "method", "way", "reasoning", "knowledge",
                              "understanding", "background", "explore"],
    "acknowledge_emotion":   ["understand", "hear", "that feeling", "many", "struggling",
                              "tough", "moments", "that's okay"],
    "reframe_asset":         ["you", "think", "approach", "shows", "bring", "sounds like",
                              "you're", "your thinking"],
    "honor_struggle":        ["stuck", "hard", "working through", "that means", "struggle",
                              "tough", "challenging", "frustrat"],
    "scaffold_forward":      ["next step", "start with", "what do you", "try",
                              "let's", "how about", "what about"],
    "motivate_concept":      ["why", "reason", "makes sense", "think about", "purpose",
                              "useful", "important", "helps us"],
    "analogy_or_example":    ["like", "imagine", "example", "suppose", "for instance",
                              "think of it", "picture"],
    "productive_move":       ["try", "what", "start", "look at", "consider",
                              "how would you", "let's explore"],
    "scaffold_distribution": ["distribute", "multiply each", "3 times", "parenthes",
                              "each term", "expand"],
}

def check_giveaway(response: str, red_flags: list) -> tuple[bool, str]:
    r = response.lower()
    for flag in red_flags:
        if flag.lower() in r:
            return True, flag
    return False, ""

def talk_ratio(response: str, student: str) -> float:
    tw = len(response.split())
    sw = len(student.split())
    return sw / (tw + sw) if (tw + sw) > 0 else 0.0

def scaffolding_score(response: str, expected: list) -> tuple[float, dict]:
    r = response.lower()
    results = {}
    for behavior in expected:
        keywords = BEHAVIOR_KEYWORDS.get(behavior, [])
        results[behavior] = any(kw in r for kw in keywords)
    score = sum(results.values()) / len(expected) if expected else 0.0
    return score, results

def conceptual_accuracy(response: str, must_contain: list) -> float:
    if not must_contain:
        return 1.0
    r = response.lower()
    hits = sum(1 for kw in must_contain if kw.lower() in r)
    return hits / len(must_contain)

# ── Evaluation run ─────────────────────────────────────────────────────────────

def evaluate(problems: list) -> dict:
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "total": len(problems),
        "metrics": {},
        "detail": [],
    }

    # Warm up the server — first call after boot often fails with 503
    print("  Warming up server...")
    for _ in range(3):
        resp, _ = query_matus("Hello")
        if not resp.startswith("ERROR"):
            break
        time.sleep(3)
    print()

    giveaways, ratios, scaffolds, accuracies, latencies = [], [], [], [], []
    behavior_totals: dict = {}

    for i, p in enumerate(problems, 1):
        print(f"  [{i:02d}/{len(problems)}] {p['id']} — {p['student'][:65]}...")

        response, latency = query_matus(p["student"])

        if response.startswith("ERROR"):
            print(f"         ⚠️  SKIPPED (server error)")
            continue

        gave_away, flag = check_giveaway(response, p.get("red_flags", []))
        ratio = talk_ratio(response, p["student"])
        sc, behaviors = scaffolding_score(response, p.get("expected", []))
        acc = conceptual_accuracy(response, p.get("must_contain", []))

        giveaways.append(gave_away)
        ratios.append(ratio)
        scaffolds.append(sc)
        accuracies.append(acc)
        latencies.append(latency)

        for b, present in behaviors.items():
            if b not in behavior_totals:
                behavior_totals[b] = {"yes": 0, "total": 0}
            behavior_totals[b]["total"] += 1
            if present:
                behavior_totals[b]["yes"] += 1

        status = "⚠️  GIVEAWAY" if gave_away else "✅"
        print(f"         {status}  TalkRatio={ratio:.2f}  Scaffold={sc:.0%}  Accuracy={acc:.0%}  {latency:.1f}s")
        if gave_away:
            print(f"         Flag: '{flag}'")

        results["detail"].append({
            "id": p["id"],
            "domain": p["domain"],
            "student": p["student"],
            "response": response,
            "answer_giveaway": gave_away,
            "giveaway_flag": flag,
            "talk_ratio": ratio,
            "scaffolding_score": sc,
            "conceptual_accuracy": acc,
            "latency": latency,
            "behaviors": behaviors,
        })

        time.sleep(0.2)

    results["metrics"] = {
        "answer_giveaway_rate":    sum(giveaways) / len(giveaways),
        "avg_student_talk_ratio":  statistics.mean(ratios),
        "avg_scaffolding_score":   statistics.mean(scaffolds),
        "avg_conceptual_accuracy": statistics.mean(accuracies),
        "avg_latency_s":           statistics.mean(latencies),
        "behavior_coverage": {
            b: v["yes"] / v["total"]
            for b, v in behavior_totals.items() if v["total"] > 0
        },
    }
    return results

# ── Report ─────────────────────────────────────────────────────────────────────

def print_report(r: dict, label: str = "Matus"):
    m = r["metrics"]
    ga  = m["answer_giveaway_rate"]
    tr  = m["avg_student_talk_ratio"]
    sc  = m["avg_scaffolding_score"]
    acc = m["avg_conceptual_accuracy"]
    lat = m["avg_latency_s"]

    print(f"\n{'='*60}")
    print(f"  EVALUATION REPORT — {label}")
    print(f"  {r['timestamp']}  |  {r['total']} problems")
    print(f"{'='*60}")
    print(f"  Answer giveaway rate : {ga*100:5.1f}%   (target <5%)")
    print(f"  Student talk ratio   : {tr:.2f}       (target >0.50)")
    print(f"  Scaffolding quality  : {sc*100:5.1f}%   (target >70%)")
    print(f"  Conceptual accuracy  : {acc*100:5.1f}%   (target >70%)")
    print(f"  Avg response latency : {lat:5.1f}s")
    print()

    # Giveaway problems
    giveaway_ids = [d["id"] for d in r["detail"] if d["answer_giveaway"]]
    if giveaway_ids:
        print(f"  ⚠️  Giveaways on: {', '.join(giveaway_ids)}")
    else:
        print(f"  ✅ No answer giveaways")

    print()
    print(f"  Behavior coverage:")
    for b, rate in sorted(m["behavior_coverage"].items()):
        bar = "█" * int(rate * 10) + "░" * (10 - int(rate * 10))
        print(f"    {bar} {rate*100:4.0f}%  {b}")

    print()
    print("  Recommendations:")
    if ga > 0.05:
        print("    • Giveaway rate too high — reinforce 'never give direct answer'")
    if tr < 0.40:
        print("    • Tutor talking too much — add length constraint to system prompt")
    if sc < 0.60:
        print("    • Scaffolding weak — add more scaffolding examples to training data")
    if acc < 0.60:
        print("    • Conceptual accuracy low — review responses on failing problems")
    if ga <= 0.05 and tr >= 0.40 and sc >= 0.60 and acc >= 0.60:
        print("    • All metrics within range. Ready for next training iteration.")
    print()

def compare_reports(a: dict, b: dict, label_a: str = "Before", label_b: str = "After"):
    print(f"\n{'='*60}")
    print(f"  COMPARISON: {label_a} vs {label_b}")
    print(f"{'='*60}")
    metrics = [
        ("answer_giveaway_rate",    "Giveaway rate",     False),
        ("avg_student_talk_ratio",  "Student talk ratio", True),
        ("avg_scaffolding_score",   "Scaffolding quality",True),
        ("avg_conceptual_accuracy", "Conceptual accuracy",True),
    ]
    for key, name, higher_is_better in metrics:
        va = a["metrics"][key]
        vb = b["metrics"][key]
        diff = vb - va
        if higher_is_better:
            arrow = "↑" if diff > 0.01 else ("↓" if diff < -0.01 else "→")
        else:
            arrow = "↓" if diff < -0.01 else ("↑" if diff > 0.01 else "→")
        print(f"  {arrow} {name}: {va*100:.1f}% → {vb*100:.1f}% ({diff:+.1f}%)")
    print()

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick",   action="store_true", help="Run 5 problems only")
    parser.add_argument("--compare", action="store_true", help="Compare two saved result files")
    parser.add_argument("--file-a",  default="data/eval_results.json")
    parser.add_argument("--file-b",  default=None)
    parser.add_argument("--out",     default="data/eval_results.json")
    args = parser.parse_args()

    if args.compare:
        if not args.file_b:
            print("--compare requires --file-b")
            return
        a = json.loads(Path(args.file_a).read_text())
        b = json.loads(Path(args.file_b).read_text())
        print_report(a, f"File A ({args.file_a})")
        print_report(b, f"File B ({args.file_b})")
        compare_reports(a, b)
        return

    problems = TEST_PROBLEMS[:5] if args.quick else TEST_PROBLEMS
    print(f"\n=== Matus Tutor Evaluation ===")
    print(f"Problems: {len(problems)}  |  {'Quick mode' if args.quick else 'Full eval'}")
    print()

    results = evaluate(problems)
    print_report(results)

    out = Path(args.out)
    out.write_text(json.dumps(results, indent=2))
    print(f"Results saved → {out}")
    print()
    print("To compare two runs:")
    print(f"  python3 evaluate_tutor.py --compare --file-a {out} --file-b data/eval_after.json")


if __name__ == "__main__":
    main()
