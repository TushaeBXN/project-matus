# tutor/memory.py
# Cross-session student memory — behavioral observations only, never deficit labels.
# Profile 4 detection requires cross-session trajectory (3+ sessions, mastery absent).
#
# Uses ChromaDB + sentence-transformers when available.
# Falls back to a lightweight JSON file store when those aren't installed
# (e.g. on older hardware with PyTorch < 2.4).

import json
import os
from datetime import datetime
from pathlib import Path

# ── Try to load ChromaDB / sentence-transformers ──────────────────────────────
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    CHROMADB_AVAILABLE = True
except Exception:
    CHROMADB_AVAILABLE = False


class StudentMemory:
    def __init__(self, db_path: str = "data/student_memory"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)

        if CHROMADB_AVAILABLE:
            self._mode = "chromadb"
            self.client  = chromadb.PersistentClient(path=str(self.db_path))
            self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        else:
            self._mode = "json"
            print("  [Memory] ChromaDB not available — using lightweight JSON store.")

    # ── JSON fallback store ───────────────────────────────────────────────────

    def _json_path(self, student_id: str) -> Path:
        return self.db_path / f"student_{student_id}.json"

    def _load_json(self, student_id: str) -> list:
        p = self._json_path(student_id)
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
        return []

    def _save_json(self, student_id: str, records: list):
        self._json_path(student_id).write_text(json.dumps(records, indent=2))

    # ── Public API ────────────────────────────────────────────────────────────

    def store_session_summary(self, student_id: str, session_id: str, summary: dict):
        """
        Store what the student DID — never what the student IS.
        mastery_absent=True in 3+ consecutive sessions → Profile 4 (Tier 2 trigger).
        """
        if self._mode == "chromadb":
            collection = self.client.get_or_create_collection(name=f"student_{student_id}")
            collection.add(
                documents=[summary.get("observations", "")],
                metadatas=[{
                    "concepts_attempted": str(summary.get("concepts", [])),
                    "approaches_used":    str(summary.get("approaches", [])),
                    "mastery_absent":     summary.get("mastery_absent", False),
                    "momentum_moments":   str(summary.get("momentum", [])),
                    "friction_moments":   str(summary.get("friction", [])),
                    "session_date":       summary.get("date", datetime.utcnow().isoformat()),
                    "session_id":         session_id,
                }],
                ids=[session_id],
            )
        else:
            records = self._load_json(student_id)
            records.append({
                "session_id":     session_id,
                "observations":   summary.get("observations", ""),
                "concepts":       summary.get("concepts", []),
                "approaches":     summary.get("approaches", []),
                "mastery_absent": summary.get("mastery_absent", False),
                "momentum":       summary.get("momentum", []),
                "friction":       summary.get("friction", []),
                "date":           summary.get("date", datetime.utcnow().isoformat()),
            })
            self._save_json(student_id, records)

    def retrieve_context(self, student_id: str, current_concept: str) -> dict:
        """
        Returns prior observations and whether Profile 4 signal is present.
        """
        try:
            if self._mode == "chromadb":
                collection = self.client.get_collection(name=f"student_{student_id}")
                results  = collection.query(query_texts=[current_concept], n_results=5)
                all_meta = collection.get()["metadatas"]
                mastery_absent_count = sum(
                    1 for m in all_meta if m.get("mastery_absent") is True
                )
                return {
                    "prior_observations": results["documents"][0] if results["documents"] else [],
                    "profile4_signal":    mastery_absent_count >= 3,
                }
            else:
                records = self._load_json(student_id)
                observations = [r["observations"] for r in records if r.get("observations")]
                mastery_absent_count = sum(
                    1 for r in records if r.get("mastery_absent") is True
                )
                return {
                    "prior_observations": observations[-5:],
                    "profile4_signal":    mastery_absent_count >= 3,
                }
        except Exception:
            return {"prior_observations": [], "profile4_signal": False}
