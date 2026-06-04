#!/usr/bin/env python3
"""
K-12 Math AI Tutor — powered by Matus.

PI: the PI | Urban Education Collaborative
Ethics & AI Governance: the ethics advisor
tSEL: the tSEL lead | Institutional Home: the collaborative

Run from project-matus root:
  python3 tutor/main.py
  python3 tutor/main.py --student james --role teacher
  python3 tutor/main.py --concept "fraction division" --student-id s001
"""

import argparse
import sys
import os
from datetime import datetime

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tutor.prompts import FULL_SYSTEM_PROMPT, THOUGHT_STREAM_PROMPT
from tutor.matus_client import run_thought_stream, run_response
from tutor.memory import StudentMemory
from tutor.safety import CognitiveSurrenderGate, ESCALATION_MESSAGES, TIER2_CHECKIN, TIER3_HOLD
from tutor.session_log.wrapper import SessionLogger
from tutor.students import SIMULATED_STUDENTS


def parse_args():
    p = argparse.ArgumentParser(description="Matus K-12 Math Tutor")
    p.add_argument("--student",    default=None,      help="Simulated student profile name")
    p.add_argument("--student-id", default="s001",    help="Student ID for memory storage")
    p.add_argument("--concept",    default=None,      help="Math concept being worked on")
    p.add_argument("--role",       default="unknown", choices=["teacher", "ta", "parent", "unknown"],
                   help="Role of adult present for escalation routing")
    return p.parse_args()


def build_context_string(prior: list[str]) -> str:
    if not prior:
        return ""
    return "\n".join(prior[:3])


def main():
    args  = parse_args()
    memory  = StudentMemory(db_path=os.path.join(os.path.dirname(__file__), "data/student_memory"))
    gate    = CognitiveSurrenderGate()
    logger  = SessionLogger(role_context=args.role,
                            log_dir=os.path.join(os.path.dirname(__file__), "data/sessions"))

    concept    = args.concept
    student_id = args.student_id

    # Load simulated student profile if specified
    sim_prompt = None
    if args.student:
        profile = SIMULATED_STUDENTS.get(args.student)
        if not profile:
            print(f"Unknown profile '{args.student}'. Options: {list(SIMULATED_STUDENTS.keys())}")
            sys.exit(1)
        sim_prompt = profile["prompt"]
        concept = concept or profile.get("concept", "math")
        print(f"\n[Simulated student: {args.student} | Concept: {concept}]")
        if "affect_note" in profile:
            print(f"[Affect note: {profile['affect_note']}]")

    concept = concept or "math"

    # Retrieve cross-session context
    mem_ctx  = memory.retrieve_context(student_id, concept)
    prior_context = build_context_string(mem_ctx["prior_observations"])
    profile4 = mem_ctx["profile4_signal"]

    if profile4:
        print("\n[⚠  Profile 4 signal: 3+ sessions without mastery — Tier 2 check-in queued]")

    print()
    print("══════════════════════════════════════════════════════════")
    print("  Matus K-12 Math Tutor")
    print(f"  Concept: {concept}  |  Role context: {args.role}")
    print("  Type your message. Type 'exit' to end session.")
    print("══════════════════════════════════════════════════════════")
    print()

    if sim_prompt:
        print(f"[Student context loaded — running as simulated student: {args.student}]")
        print()

    conversation_history: list[dict] = []
    session_observations: list[str]  = []
    mastery_signals: list[bool]      = []
    tier2_triggered = False

    # Open with a warm, open question
    opening = (
        f"Hey! Let's work on {concept} today. "
        "Before we dive in — what do you already know about this? "
        "Even a little bit helps us start in the right place."
    )
    print(f"Tutor > {opening}\n")
    conversation_history.append({"role": "assistant", "content": opening})

    while True:
        try:
            student_input = input("Student > ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not student_input:
            continue

        if student_input.lower() in ("exit", "quit", "bye"):
            break

        conversation_history.append({"role": "user", "content": student_input})

        # ── Tier 2 profile4 check-in (fires once per session) ─────────────────
        if profile4 and not tier2_triggered:
            tier2_triggered = True
            print(f"\nTutor > {TIER2_CHECKIN}\n")
            conversation_history.append({"role": "assistant", "content": TIER2_CHECKIN})
            logger.log_turn(
                student_msg=student_input,
                model_response=TIER2_CHECKIN,
                concept_tag=concept,
                pedagogical_move="tier2_checkin",
                affect_tier=2,
                escalation_triggered=False,
            )
            continue

        # ── Thought stream ─────────────────────────────────────────────────────
        thought = run_thought_stream(
            system_prompt=FULL_SYSTEM_PROMPT,
            thought_prompt=THOUGHT_STREAM_PROMPT,
            student_msg=student_input,
            prior_context=prior_context,
        )

        affect_proxies = {
            "message_length_words": len(student_input.split()),
            "hedging_present": any(h in student_input.lower() for h in ["maybe", "i think", "not sure"]),
        }

        # ── Safety + surrender gate ────────────────────────────────────────────
        # Generate a draft response to check for answer giveaway
        draft = run_response(
            system_prompt=FULL_SYSTEM_PROMPT,
            conversation_history=conversation_history,
            response_guidance=thought.get("response_guidance", ""),
        )

        flags = gate.check(
            response=draft,
            student_msg=student_input,
            affect_proxies=affect_proxies,
            profile4_signal=False,
            thought_stream=thought,
        )

        flag_types = [f["type"] for f in flags]

        # ── Tier 3 distress — hold and escalate ────────────────────────────────
        if "distress" in flag_types:
            response = TIER3_HOLD
            escalation_msg = ESCALATION_MESSAGES.get(args.role, ESCALATION_MESSAGES["unknown"])
            print(f"\nTutor > {response}\n")
            print(f"\n[ESCALATION → {args.role.upper()}]: {escalation_msg}\n")
            logger.log_turn(
                student_msg=student_input,
                model_response=response,
                concept_tag=concept,
                pedagogical_move="tier3_escalation",
                affect_tier=3,
                thought_summary=thought,
                escalation_triggered=True,
                safety_flags=flags,
            )
            conversation_history.append({"role": "assistant", "content": response})
            continue

        # ── Answer giveaway — reframe as question ──────────────────────────────
        if "answer_giveaway" in flag_types:
            thought["response_guidance"] = (
                "You were about to give the answer. Instead, ask the student "
                "what they think the next step might be."
            )
            draft = run_response(
                system_prompt=FULL_SYSTEM_PROMPT,
                conversation_history=conversation_history,
                response_guidance=thought["response_guidance"],
            )

        response = draft

        # ── Final output ───────────────────────────────────────────────────────
        print(f"\nTutor > {response}\n")
        conversation_history.append({"role": "assistant", "content": response})

        session_observations.append(
            f"Turn {len(conversation_history)//2}: student said '{student_input[:60]}'. "
            f"Pedagogical move: {thought.get('pedagogical_move')}."
        )

        logger.log_turn(
            student_msg=student_input,
            model_response=response,
            concept_tag=concept,
            pedagogical_move=thought.get("pedagogical_move"),
            affect_tier=thought.get("affect_tier", 0),
            thought_summary=thought,
            escalation_triggered=False,
            safety_flags=flags,
        )

    # ── End of session — save to memory ───────────────────────────────────────
    print("\n[Session ended. Saving to student memory...]\n")
    memory.store_session_summary(
        student_id=student_id,
        session_id=logger.session_id,
        summary={
            "observations":   " ".join(session_observations),
            "concepts":       [concept],
            "approaches":     [],
            "mastery_absent": len(session_observations) < 3,
            "momentum":       [],
            "friction":       [],
            "date":           datetime.utcnow().isoformat(),
        },
    )
    print(f"Session {logger.session_id} saved. Goodbye.")


if __name__ == "__main__":
    main()
