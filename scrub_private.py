#!/usr/bin/env python3
"""
Remove private names and institutional references from all project files.
Safe to run multiple times — idempotent.

Usage:
  python3 scrub_private.py           # preview changes
  python3 scrub_private.py --apply   # apply changes
"""

import argparse
import json
import re
from pathlib import Path

# ── What to remove / replace ──────────────────────────────────────────────────

REPLACEMENTS = [
    # Professors / collaborators
    ("Dr. Rakèta Ouédraogo-Thomas",     "the PI"),
    ("Rakèta Ouédraogo-Thomas",         "the PI"),
    ("Dr. Rummage-Massey",              "the tSEL lead"),
    ("Dr. Rummage",                     "the tSEL lead"),
    ("Rummage-Massey",                  "the tSEL lead"),
    ("Dr. Gordon Hull",                 "the ethics advisor"),
    ("Gordon Hull",                     "the ethics advisor"),
    ("Dr. Hull",                        "the ethics advisor"),

    # Institutions (keep generic)
    ("Urban Education Collaborative, UNC Charlotte",  "the Urban Education Collaborative"),
    ("UNC Charlotte",                   "the research university"),
    ("University of North Carolina at Charlotte",     "the research university"),
    ("University of North Carolina",    "the research university"),
    ("Cato College",                    "the college of education"),
    ("CHAIS",                           "the ethics center"),
    ("UEC",                             "the collaborative"),

    # Brian's university — keep only if explicitly about Brian's background
    # Full Sail stays when paired with Brian Tushae Thomas, removed otherwise
]

# Files to scrub
TARGET_EXTENSIONS = {".py", ".sh", ".md", ".txt"}
TARGET_FILES = [
    "data/raw_responses.jsonl",
    "data/matus_finetune.jsonl",
    "data/math_tutor_dataset.jsonl",
]

REPO_DIR = Path(__file__).parent


def scrub_text(text: str) -> tuple[str, list[str]]:
    changes = []
    for original, replacement in REPLACEMENTS:
        if original in text:
            count = text.count(original)
            text = text.replace(original, replacement)
            changes.append(f"  '{original}' → '{replacement}' ({count}x)")
    return text, changes


def scrub_jsonl(path: Path, apply: bool) -> int:
    if not path.exists():
        return 0
    lines = path.read_text().splitlines()
    new_lines = []
    total_changes = 0
    for line in lines:
        if not line.strip():
            new_lines.append(line)
            continue
        scrubbed, changes = scrub_text(line)
        new_lines.append(scrubbed)
        total_changes += len(changes)
    if apply and total_changes > 0:
        path.write_text("\n".join(new_lines) + "\n")
    return total_changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                        help="Apply changes (default is preview only)")
    args = parser.parse_args()

    mode = "APPLYING" if args.apply else "PREVIEW"
    print(f"=== Privacy Scrub — {mode} ===")
    print()

    total = 0

    # Scrub source files
    for ext in TARGET_EXTENSIONS:
        for path in REPO_DIR.rglob(f"*{ext}"):
            if ".git" in str(path) or "__pycache__" in str(path):
                continue
            text = path.read_text(errors="ignore")
            scrubbed, changes = scrub_text(text)
            if changes:
                print(f"{path.relative_to(REPO_DIR)}")
                for c in changes:
                    print(c)
                print()
                total += len(changes)
                if args.apply:
                    path.write_text(scrubbed)

    # Scrub data files (JSONL)
    for rel in TARGET_FILES:
        path = REPO_DIR / rel
        n = scrub_jsonl(path, apply=args.apply)
        if n > 0:
            print(f"{rel}: {n} replacements")
            total += n

    print()
    if total == 0:
        print("✅ Nothing to scrub — all clean.")
    elif args.apply:
        print(f"✅ Done. {total} replacements applied.")
    else:
        print(f"Found {total} items to replace.")
        print("Run with --apply to make changes:")
        print("  python3 scrub_private.py --apply")


if __name__ == "__main__":
    main()
