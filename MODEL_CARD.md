---
language:
- en
license: apache-2.0
tags:
- education
- math
- tutoring
- k12
- llama
- gguf
- culturally-responsive
- local
base_model: meta-llama/Llama-3.2-3B-Instruct
---

# Matus 3B — K-12 Math AI Tutor

**Built by Brian Tushae Thomas**
Independent ML/AI Developer | San Diego, California
Full Sail University — B.S. Entertainment Business

---

## What Matus Is

Matus is a fine-tuned Llama 3.2 3B model built for K-12 and early college math tutoring.
It is the backbone of Project Matus — an open-source, locally-run AI tutoring system
designed for students whose ways of knowing have historically been left out of math education.

**Core design principles:**
- Never gives answers directly — scaffolds student thinking through questions
- Recognizes valid alternative mathematical frameworks before correcting
- Protects productive struggle — does not recalibrate downward because a student is frustrated
- Culturally responsive — code-switching, family methods, and non-Western approaches are assets
- Neurodivergence-aware — short responses and flat affect are not treated as disengagement
- No data collection. No cloud. No subscriptions. Runs entirely on local hardware.

---

## What It Runs On

- **Format:** GGUF Q4_K_M quantization
- **Compatible with:** llama.cpp, Ollama, LM Studio, any GGUF-compatible runtime
- **Minimum hardware:** 8 GB RAM, any CPU (Intel, AMD, Apple Silicon)
- **Recommended:** 16 GB RAM for comfortable performance
- **Latency:** 30–90 seconds per response on CPU-only hardware. Faster on Apple Silicon or GPU.

---

## How To Run It

**With llama.cpp:**
```bash
llama-server -m matus-3b-Q4_K_M.gguf -c 3072 --port 8080 --host 127.0.0.1
```

**With the full Project Matus system:**
```bash
git clone https://github.com/TushaeBXN/project-matus.git
cd project-matus
pip install -r requirements.txt

# Place this GGUF in .models/matus-3b-Q4_K_M.gguf
# then:
./start.sh
```

**K-12 Math Tutor (with simulated student profiles):**
```bash
./boot_server.sh
python3 tutor/main.py --student james --role teacher
```

---

## Training

- **Base model:** Llama 3.2 3B Instruct (unsloth/Llama-3.2-3B-Instruct)
- **Method:** LoRA fine-tuning (r=16, lora_alpha=32)
- **Dataset:** 250 curated examples — identity data, conversational responses, K-12 and
  early college math tutoring scenarios across 9 domains
- **Training hardware:** NVIDIA RTX A6000 (48GB VRAM) via RunPod
- **Framework:** Unsloth + TRL SFTTrainer
- **Epochs:** 3

---

## Evaluation Results

Evaluated on 15 held-out math tutoring problems against a prompt-only baseline:

| Metric | Baseline | Matus 3B | Target |
|---|---|---|---|
| Answer giveaway rate | 0.0% | 0.0% | <5% |
| Scaffolding quality | 70.0% | 72.7% | >70% |
| Conceptual accuracy | 23.3% | 32.6% | >70% |
| Ends with question | 67% | 86% | — |

Behavior improvements over baseline: `honor_struggle`, `affirm_partial`,
`recognize_fallacy`, `counterexample`, `explain_composition` all moved from 0% to 100%.

Full evaluation report:
[docs/preliminary_data.md](https://github.com/TushaeBXN/project-matus/blob/main/docs/preliminary_data.md)

---

## What It Won't Do

- **No data collection** — nothing leaves your machine
- **No cloud dependency** — runs fully offline after download
- **No answer giveaways** — designed to scaffold, not solve
- **No biometric input** — affect detection is text-based only
- **No diagnostic labeling** — student memory stores behavioral observations, never deficit labels

---

## Project

Part of **Project Matus** — an open-source K-12 math tutoring platform with:
- Thought-token reasoning pipeline (internal reasoning hidden from student)
- tSEL-grounded affect detection (Tier 1/2/3 escalation)
- ChromaDB cross-session student memory (Profile 4 detection)
- Epistemically just session logging (annotation-ready for Dr. Hull's labeling protocol)
- 5 simulated student profiles for testing and co-design

GitHub: [github.com/TushaeBXN/project-matus](https://github.com/TushaeBXN/project-matus)

---

## License

Apache 2.0 — free to use, modify, and distribute with attribution.
Base model license: Llama 3.2 Community License (Meta).
