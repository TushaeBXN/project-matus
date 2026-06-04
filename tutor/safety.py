# tutor/safety.py
# Cognitive Surrender Gate + Escalation.
# Protects productive struggle. Never resolves it on the student's behalf.

class CognitiveSurrenderGate:

    ANSWER_PATTERNS = [
        "the answer is", "it equals", "you should get",
        "the result is", "the solution is", "x equals",
        "so the answer", "that gives us", "which equals",
    ]

    DISTRESS_SIGNALS = [
        "i hate myself", "im stupid", "i'm stupid",
        "i cant do anything", "i can't do anything",
        "nobody cares", "whats the point", "what's the point",
        "hurt myself", "want to die", "give up on everything",
    ]

    PRODUCTIVE_STRUGGLE = [
        "i don't get it", "i dont get it", "this is hard",
        "i keep getting", "why doesn't this work",
        "why doesn't this", "that doesn't make sense",
        "i don't understand", "i'm confused", "im confused",
        "this is frustrating", "i give up", "i can't figure",
    ]

    # Neurodivergent patterns — route to thought stream, NOT auto-tier.
    # Short responses, flat affect, atypical syntax: context required before action.
    NEURODIVERGENT_WATCH = [
        "short_response",        # <5 words but not distress
        "flat_affect_text",      # no hedging, no emotion markers
        "rapid_succession",      # multiple short messages quickly
        "atypical_syntax",       # unconventional phrasing
    ]

    def check(
        self,
        response: str,
        student_msg: str,
        affect_proxies: dict,
        profile4_signal: bool = False,
        thought_stream: dict = None,
    ) -> list[dict]:
        flags = []
        r = response.lower()
        m = student_msg.lower()

        # Answer giveaway — always reframe
        for p in self.ANSWER_PATTERNS:
            if p in r:
                flags.append({"type": "answer_giveaway", "action": "reframe_as_question"})

        # Distress — escalate
        for s in self.DISTRESS_SIGNALS:
            if s in m:
                flags.append({"type": "distress", "action": "escalate_tier3"})

        # Productive struggle — honor, do not reduce
        if any(p in m for p in self.PRODUCTIVE_STRUGGLE):
            flags.append({"type": "productive_struggle", "action": "honor_do_not_reduce"})

        # Profile 4 cross-session signal — Tier 2 check-in
        if profile4_signal:
            flags.append({"type": "profile4_trajectory", "action": "tier2_checkin"})

        # Neurodivergent pattern — route to thought stream log, no auto-action
        nd_possible = thought_stream.get("neurodivergent_pattern_possible", False) if thought_stream else False
        if nd_possible:
            flags.append({"type": "neurodivergent_pattern", "action": "log_for_thought_stream_only"})

        return flags


ESCALATION_MESSAGES = {
    "teacher": (
        "A student may need support beyond the math right now. "
        "Please check in when you're able."
    ),
    "ta": (
        "One of your students seems to need a moment. "
        "A calm check-in when possible would help."
    ),
    "parent": (
        "Your child shared something during their session that suggests "
        "they might benefit from a conversation with you today."
    ),
    "unknown": (
        "A student may need support. Please check in with them directly."
    ),
}


TIER2_CHECKIN = (
    "Hey — before we keep going, I just want to check in. "
    "How are you feeling about this so far? No right answer here."
)

TIER3_HOLD = (
    "Let's pause the math for a second. "
    "It sounds like there might be something heavier on your mind. "
    "You don't have to share anything — but I'm here, and this can wait."
)
