# tutor/logging/wrapper.py
# Session logger — every turn logged with annotation fields.
# Annotator metadata travels with every label.

import json
import uuid
import os
from datetime import datetime


class SessionLogger:
    def __init__(self, role_context: str = "unknown", log_dir: str = "data/sessions"):
        self.session_id  = str(uuid.uuid4())[:8]
        self.turn_number = 0
        self.role_context = role_context
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    def log_turn(
        self,
        student_msg: str,
        model_response: str,
        concept_tag:         str  = None,
        pedagogical_move:    str  = None,
        affect_tier:         int  = None,
        thought_summary:     dict = None,
        escalation_triggered: bool = False,
        safety_flags:        list = None,
    ) -> dict:
        self.turn_number += 1
        m = student_msg.lower()

        turn = {
            "session_id":    self.session_id,
            "turn":          self.turn_number,
            "timestamp":     datetime.utcnow().isoformat(),
            "role_context":  self.role_context,
            "student_message": student_msg,
            "model_response":  model_response,
            "concept_tag":     concept_tag,
            "pedagogical_move": pedagogical_move,
            "affect_proxies": {
                "message_length_words":   len(student_msg.split()),
                "hedging_present":        any(h in m for h in ["maybe", "i think", "not sure", "i guess"]),
                "code_switching_present": None,
                "repair_attempt":         any(r in m for r in ["wait", "actually", "no wait", "i mean"]),
                "latency_flag":           None,
            },
            "affect_tier_triggered":   affect_tier,
            "thought_stream_summary":  thought_summary,
            "safety_flags":            safety_flags or [],
            "escalation_triggered":    escalation_triggered,
            # Annotation fields — filled by annotators, not the system
            "annotation": {
                "move_quality":                  None,
                "error_type":                    None,
                "mathematical_framework":        None,
                "annotator_framework":           None,
                "annotator_confidence":          None,
                "disagreement_flag":             False,
                "disagreement_notes":            None,
                "neurodivergent_pattern_possible": None,
                "new_category_proposed":         None,
                "notes":                         None,
            },
        }

        path = os.path.join(self.log_dir, f"{self.session_id}.jsonl")
        with open(path, "a") as f:
            f.write(json.dumps(turn) + "\n")

        return turn
