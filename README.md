# Project Matus

A unified, local AI system built by **Brian T. Thomas** in collaboration with **Dr. Raketa Ouedraogo-Thomas** — independent ML/AI developer from San Diego, California, and graduate of Full Sail University with a Bachelor of Science in Entertainment Business.

Project Matus runs entirely on your own hardware. No cloud. No subscriptions. No data leaving your machine.

---

## What It Is

Project Matus is two things:

**1. Matus — a custom fine-tuned AI model**
A Llama 3.2 3B model fine-tuned using LoRA on domain-specific training data. Brian T. Thomas is baked into the weights as creator. The model is publicly available on HuggingFace and runs locally via llama.cpp with no internet connection required after download.

**2. A K-12 Math AI Tutor**
Built on top of Matus as the backbone, the tutor system implements a full pedagogical pipeline: thought-token reasoning, affect detection, cross-session student memory, and an epistemically just session logging system designed for culturally responsive math education.

---

## Get Matus Running — One Command

If you have Ollama installed:

```bash
ollama run hf.co/TushaeBXN/matus-3b:Q4_K_M
```

Or clone the full system (auto-downloads the model on first run):

```bash
git clone https://github.com/TushaeBXN/project-matus.git
cd project-matus
pip install -r requirements.txt
chmod +x start.sh boot_server.sh
./start.sh
```

---

## Model

**Matus 3B — K-12 Math AI Tutor**
HuggingFace: [huggingface.co/TushaeBXN/matus-3b](https://huggingface.co/TushaeBXN/matus-3b)

- **Base:** Llama 3.2 3B Instruct
- **Method:** LoRA fine-tuning (r=16, lora_alpha=32)
- **Training hardware:** NVIDIA RTX A6000 (48GB VRAM) via RunPod
- **Framework:** Unsloth + TRL SFTTrainer
- **Dataset:** 250 curated examples — identity, conversational, K-12 and early college math tutoring across 9 domains
- **Format:** GGUF Q4_K_M (~2GB)
- **Epochs:** 3

---

## Requirements

- **macOS** (Intel or Apple Silicon), Linux, or Windows
- **Python 3.10+**
- **Ollama** — [ollama.com](https://ollama.com) — easiest way to run Matus
- **llama.cpp** — via Homebrew (`brew install llama.cpp`) for the full system
- ~2 GB free disk space
- 8 GB RAM minimum (16 GB recommended)

> ⚠️ **Latency note:** On CPU-only hardware expect 30–90 seconds per response. This is normal — all inference runs locally. Apple Silicon and dedicated GPUs are significantly faster.

---

## K-12 Math Tutor

```bash
# Boot the server
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

## Architecture

```
main.py                    — Matus chat interface
tutor/
  main.py                  — Tutor entry point
  matus_client.py          — Thought stream + response pipeline
  memory.py                — Cross-session student memory (ChromaDB / JSON fallback)
  safety.py                — Cognitive surrender gate + escalation tiers
  prompts.py               — System prompts and thought stream template
  students.py              — 5 simulated student profiles
  session_log/             — Session logger with annotation fields
start.sh                   — Boot Matus (auto-downloads model on first run)
boot_server.sh             — Boot server only (background mode)
evaluate_tutor.py          — Evaluation pipeline (15 held-out problems)
generate_math_dataset.py   — Math tutor training data generator
finetune_runpod.py         — RunPod fine-tuning script (LoRA + GGUF export)
trim_dataset.py            — Dataset quality filter
build_dataset.py           — Merge and format training data
docs/
  preliminary_data.md      — Evaluation results and session findings
```

---

## Evaluation Results

Evaluated on 15 held-out math tutoring problems:

| Metric | Baseline | Matus 3B | Target |
|---|---|---|---|
| Answer giveaway rate | 0.0% | 0.0% | <5% |
| Scaffolding quality | 70.0% | 72.7% | >70% |
| Conceptual accuracy | 23.3% | 32.6% | >70% |
| Ends with question | 67% | 86% | — |

Full report: [docs/preliminary_data.md](docs/preliminary_data.md)

---

## Retrain Matus

To generate new training data and retrain:

```bash
# 1. Generate data (server must be running)
./boot_server.sh
python3 generate_training_data.py
python3 generate_math_dataset.py --passes 20
./boot_server.sh stop

# 2. Filter and build dataset
python3 trim_dataset.py --apply
python3 build_dataset.py

# 3. Fine-tune on RunPod
# Upload data/matus_finetune.jsonl and finetune_runpod.py
# Run: python3 finetune_runpod.py
# Download the GGUF and place in .models/matus-3b-Q4_K_M.gguf
```

---

## Built By

**Brian T. Thomas** in collaboration with **Dr. Raketa Ouedraogo-Thomas**
Independent ML/AI Developer | San Diego, California
Full Sail University — B.S. Entertainment Business
GitHub: [@TushaeBXN](https://github.com/TushaeBXN)
HuggingFace: [huggingface.co/TushaeBXN](https://huggingface.co/TushaeBXN)
