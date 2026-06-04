#!/bin/bash
# Boot llama.cpp server only — stays running in background.
# Use this when you need Matus available for scripts (training data, tutor, etc.)
# To stop: ./boot_server.sh stop

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$REPO_DIR/.bin"
MODELS_DIR="$REPO_DIR/.models"
GGUF_PATH="$MODELS_DIR/self-after-dark-3b.Q4_K_M.gguf"
PID_FILE="$BIN_DIR/llama.pid"
LOG_FILE="$BIN_DIR/llama.log"

if command -v llama-server &>/dev/null; then
    LLAMA_SERVER="$(command -v llama-server)"
else
    LLAMA_SERVER="$BIN_DIR/llama-server"
fi

stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        kill "$PID" 2>/dev/null && echo "🔌 Matus server stopped (PID $PID)." || echo "⚠️  Process not found."
        rm -f "$PID_FILE"
    else
        echo "No PID file found — server may not be running."
    fi
    exit 0
}

[ "${1:-}" = "stop" ] && stop_server

# Already running?
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ Matus server already running on port 8080."
    exit 0
fi

if [ ! -f "$GGUF_PATH" ]; then
    echo "❌ GGUF not found at $GGUF_PATH. Run ./start.sh first to download it."
    exit 1
fi

mkdir -p "$BIN_DIR"

echo "🚀 Starting Matus server in background on port 8080..."
"$LLAMA_SERVER" \
    -m "$GGUF_PATH" \
    -c 3072 \
    --threads 4 \
    --threads-batch 4 \
    --batch-size 128 \
    --port 8080 \
    --host 127.0.0.1 \
    > "$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"

# Wait for ready
printf "⏳ Waiting for server"
for i in $(seq 1 30); do
    if curl -s http://localhost:8080/health >/dev/null 2>&1; then
        echo " ready!"
        echo "✅ Matus server running (PID $(cat "$PID_FILE"))."
        echo "   To stop: ./boot_server.sh stop"
        exit 0
    fi
    printf "."
    sleep 2
done

echo ""
echo "❌ Server did not become ready. Check $LOG_FILE"
exit 1
