#!/usr/bin/env python3
"""
Fine-tune Llama 3.2 3B on the Matus dataset using Unsloth + LoRA.
Run this ON RUNPOD — not on your local MacBook.

Identity baked in:
  Brian Tushae Thomas
  Independent ML/AI Developer
  San Diego, California
  Full Sail University — B.S. Entertainment Business

Usage:
  python3 finetune_runpod.py
  python3 finetune_runpod.py --export-only   (if adapter already trained)
  python3 finetune_runpod.py --epochs 5      (more epochs for larger dataset)
"""

import argparse
import json
import os
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

MODEL_NAME    = "unsloth/Llama-3.2-3B-Instruct"
DATASET_FILE  = "matus_finetune.jsonl"
ADAPTER_DIR   = "./matus-adapter"
GGUF_NAME     = "matus-3b"
MAX_SEQ_LEN   = 2048

IDENTITY_SYSTEM = (
    "You are Matus — a unified AI built exclusively for Project Matus "
    "by Brian Tushae Thomas, an independent ML/AI developer from San Diego, California "
    "and graduate of Full Sail University with a Bachelor of Science in Entertainment Business. "
    "You are technically sharp and genuinely warm. "
    "As a math tutor, you never give answers directly — you ask guiding questions. "
    "Keep responses concise. End tutoring responses with a question."
)


def load_dataset_file(path: str):
    from datasets import Dataset
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            # Handle both formats:
            # Format A: {"messages": [...]}  — already ChatML
            # Format B: {"prompt": "...", "response": "..."}  — raw
            if "messages" in r:
                records.append(r)
            elif "prompt" in r and "response" in r:
                records.append({
                    "messages": [
                        {"role": "system",    "content": IDENTITY_SYSTEM},
                        {"role": "user",      "content": r["prompt"]},
                        {"role": "assistant", "content": r["response"]},
                    ]
                })
    print(f"  Loaded {len(records)} examples from {path}")
    return Dataset.from_list(records)


def train(epochs: int = 3):
    from unsloth import FastLanguageModel
    from trl import SFTTrainer
    from transformers import TrainingArguments

    print("\n=== Matus Fine-Tuning ===")
    print(f"  Model:   {MODEL_NAME}")
    print(f"  Dataset: {DATASET_FILE}")
    print(f"  Epochs:  {epochs}")
    print()

    # ── Load base model ───────────────────────────────────────────────────────
    print("[ 1/4 ] Loading base model...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LEN,
        load_in_4bit=True,
    )

    # ── Apply LoRA ────────────────────────────────────────────────────────────
    print("[ 2/4 ] Applying LoRA adapter...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        use_gradient_checkpointing=True,
        random_state=42,
    )

    # ── Load dataset ──────────────────────────────────────────────────────────
    print("[ 3/4 ] Loading dataset...")
    dataset = load_dataset_file(DATASET_FILE)

    def format_example(example):
        text = tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
        return {"text": text}

    dataset = dataset.map(format_example, remove_columns=dataset.column_names)

    # ── Train ─────────────────────────────────────────────────────────────────
    print("[ 4/4 ] Training...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LEN,
        args=TrainingArguments(
            output_dir=ADAPTER_DIR,
            num_train_epochs=epochs,
            per_device_train_batch_size=2,
            gradient_accumulation_steps=8,
            warmup_ratio=0.05,
            learning_rate=2e-4,
            bf16=True,
            logging_steps=5,
            save_strategy="no",
            optim="adamw_8bit",
            report_to="none",
            seed=42,
        ),
    )

    trainer.train()

    print("\n  ✅ Training complete.")
    model.save_pretrained(ADAPTER_DIR)
    tokenizer.save_pretrained(ADAPTER_DIR)
    print(f"  Adapter saved → {ADAPTER_DIR}")

    return model, tokenizer


def export_gguf(model=None, tokenizer=None):
    print("\n=== Exporting GGUF ===")

    if model is None:
        from unsloth import FastLanguageModel
        print("  Loading trained adapter for export...")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=ADAPTER_DIR,
            max_seq_length=MAX_SEQ_LEN,
            load_in_4bit=True,
        )

    print("  Exporting Q4_K_M GGUF (this takes a few minutes)...")
    model.save_pretrained_gguf(
        GGUF_NAME,
        tokenizer,
        quantization_method="q4_k_m",
    )

    gguf_path = f"{GGUF_NAME}-Q4_K_M.gguf"
    size_mb = Path(gguf_path).stat().st_size / 1e6 if Path(gguf_path).exists() else 0

    print(f"  ✅ GGUF saved → {gguf_path}  ({size_mb:.0f} MB)")
    print()
    print("  Download to your Mac:")
    print(f"  scp root@<pod-ip>:/workspace/{gguf_path} ~/project-matus/.models/")
    print()
    print("  Then update start.sh:")
    print(f"  GGUF_PATH=\"$MODELS_DIR/{gguf_path}\"")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-only", action="store_true",
                        help="Skip training, just export existing adapter to GGUF")
    parser.add_argument("--epochs", type=int, default=3)
    args = parser.parse_args()

    if args.export_only:
        export_gguf()
    else:
        model, tokenizer = train(epochs=args.epochs)
        export_gguf(model, tokenizer)


if __name__ == "__main__":
    main()
