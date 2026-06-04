# Project Matus

A unified, local AI system built by **Brian Tushae Thomas** — independent ML/AI developer from San Diego, California, and graduate of Full Sail University with a Bachelor of Science in Entertainment Business.

Project Matus runs entirely on your own hardware. No cloud. No subscriptions. No data leaving your machine.

---

## What It Is

Project Matus is two things:

**1. Matus — a custom fine-tuned AI model**
A Llama 3.2 3B model fine-tuned using LoRA on domain-specific training data. Brian Tushae Thomas is baked into the weights as creator. The model runs locally via llama.cpp with no internet connection required.

**2. A K-12 Math AI Tutor**
Built on top of Matus as the backbone, the tutor system implements a full pedagogical pipeline: thought-token reasoning, tSEL-grounded affect detection, cross-session student memory, and an epistemically just session logging system designed for culturally responsive math education.

---

## Architecture

```
main.py              — Matus chat interface (single unified model)
tutor/               — K-12 Math AI Tutor system
  main.py            — Tutor entry point (simulated student profiles)
  matus_client.py    — Thought stream + response pipeline
  memory.py          — Cross-session student memory (ChromaDB / JSON fallback)
  safety.py          — Cognitive surrender gate + escalation tiers
  prompts.py         — System prompts and thought stream reasoning template
  students.py        — 5 simulated student profiles
  session_log/       — Epistemically just session logger
start.sh             — Boot Matus (llama.cpp server + chat)
boot_server.sh       — Boot server only (background, for scripts)
evaluate_tutor.py    — Evaluation pipeline (15 held-out problems)
generate_math_dataset.py  — Math tutor training data generator
finetune_runpod.py   — RunPod fine-tuning script (LoRA + GGUF export)
trim_dataset.py      — Dataset quality filter
build_dataset.py     — Merge and format training data
docs/
  preliminary_data.md — Proposal-ready evaluation results
```

---

## Model

The Matus model is a fine-tuned Llama 3.2 3B (Q4_K_M quantization) trained with LoRA on 250 curated examples including:
- Identity and conversational data
- K-12 and early college math tutoring scenarios
- Scaffolding behavior examples across 9 mathematical domains

Training was conducted on an NVIDIA RTX A6000 using Unsloth. The GGUF is not included in this repository — it must be trained using `finetune_runpod.py` or downloaded separately.

---

## Requirements

- **macOS** (Intel or Apple Silicon), Linux, or Windows (WSL2)
- **Python 3.10+**
- **llama.cpp** — via Homebrew (`brew install llama.cpp`) or auto-downloaded by `start.sh`
- ~2 GB free disk space for model weights
- 8 GB RAM minimum (16 GB recommended)

> ⚠️ **Latency note:** On CPU-only hardware expect 30–90 seconds per response. This is normal — all inference runs locally. Apple Silicon and dedicated GPUs will be significantly faster.

> ⚠️ **Model weights note:** The fine-tuned Matus GGUF (`matus-3b-Q4_K_M.gguf`) is not included in this repository. You have two options:
> - **Train your own:** Use `finetune_runpod.py` with your own dataset on RunPod (~$0.50, ~15 minutes on an RTX 3090). See the Training Pipeline section below.
> - **Use the base model:** Download any compatible Llama 3.2 3B Q4_K_M GGUF from HuggingFace, place it in `.models/`, and update `GGUF_PATH` in `start.sh`.

---

## Quickstart

```bash
git clone https://github.com/TushaeBXN/project-matus.git
cd project-matus
pip install -r requirements.txt
chmod +x start.sh boot_server.sh

# Place your GGUF in .models/ first — see Model Weights note above
./start.sh
```

---

## K-12 Math Tutor

```bash
# Boot the server first
./boot_server.sh

# Run with a simulated student profile
python3 tutor/main.py --student james --role teacher
python3 tutor/main.py --student amara --role ta
python3 tutor/main.py --student devon --role teacher

# Run with a real student
python3 tutor/main.py --concept "fraction division" --student-id s001 --role teacher
```

**Simulated student profiles:**
| Profile | Grade | Concept | Key characteristic |
|---|---|---|---|
| Amara | 8 | Linear equations | Geometric/spatial reasoning |
| Miguel | 6 | Fraction division | Bilingual, family business context |
| James | 7 | Integers | Math anxiety, withholds to feel safe |
| Sera | 5 | Multiplication/area | Needs why before how |
| Devon | 6 | Order of operations | Neurodivergent, short rapid responses |

> All profiles are working drafts requiring community educator review before use in live testing.

---

## Training Pipeline

```bash
# 1. Boot server
./boot_server.sh

# 2. Generate training data
python3 generate_training_data.py
python3 generate_math_dataset.py --passes 20

# 3. Build and filter dataset
python3 trim_dataset.py --apply
python3 build_dataset.py

# 4. Stop server
./boot_server.sh stop

# 5. Fine-tune on RunPod
# Upload data/matus_finetune.jsonl and finetune_runpod.py to RunPod
# Run: python3 finetune_runpod.py
# Download the output GGUF to .models/matus-3b-Q4_K_M.gguf
```

---

## Evaluation

```bash
./boot_server.sh
python3 evaluate_tutor.py
./boot_server.sh stop
```

**Baseline results (fine-tuned Matus vs. prompt-only baseline):**

| Metric | Baseline | Fine-tuned Matus | Target |
|---|---|---|---|
| Answer giveaway rate | 0.0% | 0.0% | <5% |
| Scaffolding quality | 70.0% | 72.7% | >70% |
| Conceptual accuracy | 23.3% | 32.6% | >70% |
| ends_with_question | 67% | 86% | — |

Full evaluation report: [`docs/preliminary_data.md`](docs/preliminary_data.md)

---

## Built By

**Brian Tushae Thomas**
Independent ML/AI Developer
San Diego, California
Full Sail University — B.S. Entertainment Business
GitHub: [@TushaeBXN](https://github.com/TushaeBXN)
