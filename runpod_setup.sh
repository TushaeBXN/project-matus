#!/bin/bash
# RunPod setup script — run this INSIDE the RunPod terminal after pod starts.
# Installs everything needed for Matus fine-tuning.

set -e

echo "=== Matus RunPod Setup ==="
echo ""

# ── 1. Install Python deps ────────────────────────────────────────────────────
echo "[ 1/5 ] Installing dependencies..."
pip install -q unsloth trl datasets transformers peft accelerate bitsandbytes
echo "  ✅ Dependencies installed"
echo ""

# ── 2. Verify GPU ─────────────────────────────────────────────────────────────
echo "[ 2/5 ] Checking GPU..."
python3 -c "
import torch
print(f'  CUDA available: {torch.cuda.is_available()}')
print(f'  GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')
print(f'  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB' if torch.cuda.is_available() else '')
"
echo ""

# ── 3. Check dataset ──────────────────────────────────────────────────────────
echo "[ 3/5 ] Checking dataset..."
if [ -f "matus_finetune.jsonl" ]; then
    COUNT=$(wc -l < matus_finetune.jsonl)
    echo "  ✅ matus_finetune.jsonl found — $COUNT examples"
else
    echo "  ❌ matus_finetune.jsonl not found."
    echo "     Upload it with: scp data/matus_finetune.jsonl root@<pod-ip>:/workspace/"
    exit 1
fi
echo ""

# ── 4. Check finetune script ──────────────────────────────────────────────────
echo "[ 4/5 ] Checking finetune script..."
if [ -f "finetune_runpod.py" ]; then
    echo "  ✅ finetune_runpod.py found"
else
    echo "  ❌ finetune_runpod.py not found."
    echo "     Upload it with: scp finetune_runpod.py root@<pod-ip>:/workspace/"
    exit 1
fi
echo ""

# ── 5. Ready ──────────────────────────────────────────────────────────────────
echo "[ 5/5 ] Ready to train."
echo ""
echo "  Run:  python3 finetune_runpod.py"
echo "  Then: python3 finetune_runpod.py --export-only   (if training already done)"
echo ""
echo "  After training completes, download the GGUF:"
echo "  scp root@<pod-ip>:/workspace/matus-3b-Q4_K_M.gguf ~/Desktop/anthos-repo/.models/"
