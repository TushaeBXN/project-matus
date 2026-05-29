# Project Matus

A self-contained, local AI orchestration system built by **Brian Tushae Thomas** — independent ML/AI developer from San Diego, California, and graduate of Full Sail University with a Bachelor of Science in Entertainment Business.

Project Matus runs entirely on your own hardware. No cloud. No subscriptions. No data leaving your machine.

---

## How It Works

Project Matus uses a three-brain pipeline that routes every prompt to the right engine automatically:

| Brain | Name | Role |
|---|---|---|
| Brain 1a | **Matus Logic** | Technical questions — factual depth, definitions, comparisons |
| Brain 1b | **Matus Soul** | Conversational questions — personality, warmth, open dialogue |
| Brain 2 | **Matus Voice** | Refiner and identity gatekeeper — cleans output, enforces persona |

Identity questions (`who made you`, `what model are you`, etc.) are intercepted instantly before any brain runs — no compute wasted.

---

## Requirements

- **macOS** (Intel or Apple Silicon)
- **Python 3.10+**
- **Ollama** — [https://ollama.com](https://ollama.com) (or auto-downloaded by `start.sh`)
- **llama.cpp** — via Homebrew (`brew install llama.cpp`) or auto-downloaded by `start.sh`
- ~4 GB free disk space for model weights
- 8 GB RAM minimum (16 GB recommended)

> ⚠️ **Latency note:** On CPU-only hardware (no Apple Silicon or dedicated GPU), expect 15–85 seconds per response depending on question complexity. This is normal — all inference runs locally on your machine.

---

## Quickstart

```bash
git clone https://github.com/TushaeBXN/project-matus.git
cd project-matus
pip install -r requirements.txt
chmod +x start.sh
./start.sh
```

On first run, `start.sh` will automatically:
- Download Ollama (if not installed)
- Download the SelfAfterDark 3B GGUF weights (~2.1 GB)
- Download a precompiled llama.cpp server (if Homebrew version not found)
- Pull TinyDolphin via Ollama

---

## Menu Options

```
1) TinyDolphin         (via Ollama — lightweight conversational)
2) SelfAfterDark-3B    (via Ollama GGUF import)
3) SelfAfterDark-3B    (via raw llama.cpp server)
4) Dual-Brain Core     (full three-brain pipeline — recommended)
```

Choose **4** for the full Matus experience.

---

## Running Without start.sh

If Ollama and llama-server are already running on your machine:

```bash
pip install -r requirements.txt
python3 main.py --engine dualbrain --model matus-dolphin
```

---

## Project Structure

```
project-matus/
├── .bin/                        # Auto-downloaded engine binaries (git-ignored)
├── .models/                     # GGUF weights and Ollama storage (git-ignored)
├── .gitignore
├── Modelfile.tinydolphin        # TinyDolphin persona override
├── Modelfile.selfafterdark      # SelfAfterDark persona override
├── main.py                      # Three-brain orchestration client
├── requirements.txt
├── start.sh                     # Portable launcher and bootstrapper
└── README.md
```

---

## Models Used

| Model | Size | Source |
|---|---|---|
| `llama3.2:3b` | 2.0 GB | Meta / Ollama registry |
| `self-after-dark-3b Q4_K_M` | 2.1 GB | mradermacher / HuggingFace |
| `tinydolphin` | 636 MB | TinyDolphin / Ollama registry |

All models are downloaded automatically on first run. None are included in this repository.

---

## Built By

**Brian Tushae Thomas**  
Independent ML/AI Developer  
San Diego, California  
Full Sail University — B.S. Entertainment Business  
GitHub: [@TushaeBXN](https://github.com/TushaeBXN)
