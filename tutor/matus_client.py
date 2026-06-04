# tutor/matus_client.py
# All LLM calls route through Matus (llama.cpp on port 8080).
# Two call types: thought stream (internal) and response (student-facing).

import json
import requests

MATUS_URL = "http://localhost:8080/v1/chat/completions"
STOP_TOKENS = ["\nUser:", "\nuser:", "<|end_of_text|>", "<|im_end|>", "</s>"]


def _call(messages: list[dict], max_tokens: int = 300, temperature: float = 0.35) -> str:
    payload = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "repeat_penalty": 1.15,
        "stop": STOP_TOKENS,
        "stream": False,
    }
    try:
        r = requests.post(MATUS_URL, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        return "ERROR: Cannot reach Matus engine on port 8080."
    except requests.exceptions.Timeout:
        return "ERROR: Matus engine timed out."
    except Exception as e:
        return f"ERROR: {e}"


def run_thought_stream(
    system_prompt: str,
    thought_prompt: str,
    student_msg: str,
    prior_context: str = "",
) -> dict:
    """
    Internal reasoning pass — never shown to student.
    Returns parsed JSON or a safe fallback dict.
    """
    context_block = f"\nPrior session context:\n{prior_context}\n" if prior_context else ""
    messages = [
        {"role": "system", "content": thought_prompt},
        {"role": "user",   "content": f"{context_block}Student just said: {student_msg}"},
    ]
    raw = _call(messages, max_tokens=200, temperature=0.2)
    try:
        # Extract JSON even if model wraps it in prose
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        return json.loads(raw[start:end]) if start != -1 else _fallback_thought()
    except Exception:
        return _fallback_thought()


def run_response(
    system_prompt: str,
    conversation_history: list[dict],
    response_guidance: str,
) -> str:
    """
    Student-facing response — shaped by thought stream guidance.
    Only sends last 4 turns to avoid context overflow on CPU.
    """
    guided_system = system_prompt
    if response_guidance:
        guided_system += f"\n\nINTERNAL GUIDANCE (do not reveal): {response_guidance}"

    # Cap history to last 4 messages (2 exchanges) to stay within context window
    recent_history = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history
    messages = [{"role": "system", "content": guided_system}] + recent_history
    return _call(messages, max_tokens=120, temperature=0.4)


def _fallback_thought() -> dict:
    return {
        "student_state": "unclear",
        "math_analysis": "unclear",
        "pedagogical_move": "scaffold",
        "affect_tier": 0,
        "safety_flag": False,
        "neurodivergent_pattern_possible": False,
        "response_guidance": "Ask the student to share their thinking so far.",
    }
