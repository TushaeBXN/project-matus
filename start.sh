#!/bin/bash
set -euo pipefail

# ─── Paths and Environment ───────────────────────────────────────────────────
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$REPO_DIR/.bin"
MODELS_DIR="$REPO_DIR/.models"

# Isolate both storage AND host port to prevent conflicts with global Ollama
export OLLAMA_MODELS="$MODELS_DIR/ollama_storage"
export OLLAMA_HOST="127.0.0.1:11435"

OLLAMA_EXE="$BIN_DIR/ollama"
# Prefer system llama-server (Homebrew) — portable download is a fallback
if command -v llama-server &>/dev/null; then
    LLAMA_SERVER="$(command -v llama-server)"
else
    LLAMA_SERVER="$BIN_DIR/llama-server"
fi
GGUF_PATH="$MODELS_DIR/matus-3b-Q4_K_M.gguf"
# Using mradermacher's public open-source repository (does not require login/auth)
GGUF_URL="https://huggingface.co/mradermacher/self-after-dark-3b-GGUF/resolve/main/matus-3b-Q4_K_M.gguf"

mkdir -p "$BIN_DIR" "$MODELS_DIR" "$OLLAMA_MODELS"

# ─── Helper: download_ollama ──────────────────────────────────────────────────
download_ollama() {
    if [ -f "$OLLAMA_EXE" ]; then
        return 0
    fi
    echo "📥 Downloading standalone Ollama macOS engine..."
    curl -fL "https://ollama.com/download/Ollama-darwin.zip" -o "$BIN_DIR/Ollama-darwin.zip"
    unzip -q "$BIN_DIR/Ollama-darwin.zip" -d "$BIN_DIR"
    
    # Extract the CLI binary from the app bundle
    if [ -f "$BIN_DIR/Ollama.app/Contents/Resources/ollama" ]; then
        mv "$BIN_DIR/Ollama.app/Contents/Resources/ollama" "$BIN_DIR/"
    elif [ -f "$BIN_DIR/Ollama.app/Contents/MacOS/ollama" ]; then
        mv "$BIN_DIR/Ollama.app/Contents/MacOS/ollama" "$BIN_DIR/"
    fi
    rm -rf "$BIN_DIR/Ollama-darwin.zip" "$BIN_DIR/Ollama.app"
    chmod +x "$OLLAMA_EXE"
    echo "✅ Ollama engine ready."
}

# ─── Helper: wait_for_url ────────────────────────────────────────────────────
wait_for_url() {
    local url="$1"
    local retries=30
    echo -n "⏳ Waiting for server"
    until curl -s "$url" > /dev/null 2>&1; do
        sleep 1
        echo -n "."
        retries=$((retries - 1))
        if [ $retries -le 0 ]; then
            echo ""
            echo "❌ Server did not respond in time. Check logs."
            exit 1
        fi
    done
    echo " ready!"
}

# ─── Helper: download_gguf ───────────────────────────────────────────────────
download_gguf() {
    if [ -f "$GGUF_PATH" ]; then
        return 0
    fi
    echo "📥 Downloading SelfAfterDark GGUF weights (~2.2 GB, this may take a while)..."
    curl -fL "$GGUF_URL" -o "$GGUF_PATH"
    echo "✅ GGUF weights saved to $GGUF_PATH"
}

# ─── Helper: download_llamacpp ───────────────────────────────────────────────
download_llamacpp() {
    if [ -f "$LLAMA_SERVER" ]; then
        return 0
    fi
    echo "📥 Resolving latest llama.cpp release..."
    LATEST_TAG=$(curl -sL "https://api.github.com/repos/ggerganov/llama.cpp/releases?per_page=1" \
        | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['tag_name'])")
    if [ -z "$LATEST_TAG" ]; then
        echo "⚠️  Could not resolve latest llama.cpp tag. Check your connection."
        exit 1
    fi
    echo "   Found release: $LATEST_TAG"
    ARCH=$(uname -m)
    if [ "$ARCH" = "arm64" ]; then
        LLAMA_ARCH="arm64"
    else
        LLAMA_ARCH="x64"
    fi
    TARBALL="llama-${LATEST_TAG}-bin-macos-${LLAMA_ARCH}.tar.gz"
    LLAMA_URL="https://github.com/ggerganov/llama.cpp/releases/download/${LATEST_TAG}/${TARBALL}"
    echo "📥 Downloading llama.cpp server ($TARBALL)..."
    curl -fL "$LLAMA_URL" -o "$BIN_DIR/llama.tar.gz" || {
        echo "⚠️  Download failed: $LLAMA_URL"
        echo "    Please manually place a 'llama-server' binary in .bin/"
        exit 1
    }
    tar -xzf "$BIN_DIR/llama.tar.gz" -C "$BIN_DIR" --strip-components=0 2>/dev/null
    # Find and promote llama-server wherever it landed
    FOUND=$(find "$BIN_DIR" -name "llama-server" -not -path "$LLAMA_SERVER" | head -1)
    if [ -n "$FOUND" ] && [ "$FOUND" != "$LLAMA_SERVER" ]; then
        mv "$FOUND" "$LLAMA_SERVER"
    fi
    rm -f "$BIN_DIR/llama.tar.gz"
    chmod +x "$LLAMA_SERVER"
    echo "✅ llama-server ready ($LATEST_TAG / macos-$LLAMA_ARCH)."
}

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║              Project Matus — Starting            ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ─── Helper: start standalone, isolated Ollama server ───────────────────────
start_ollama() {
    # Check if our custom isolated port is already bound
    if lsof -Pi :11435 -sTCP:LISTEN -t >/dev/null ; then
        echo "✅ Standalone Ollama already running on isolated port 11435."
        if [ -f "$OLLAMA_EXE" ]; then
            OLLAMA_CMD=("$OLLAMA_EXE")
        else
            OLLAMA_CMD=("ollama")
        fi
        OLLAMA_PID=""
        return 0
    fi

    download_ollama
    echo "🚀 Starting portable Ollama server on isolated port 11435..."
    "$OLLAMA_EXE" serve > "$BIN_DIR/ollama.log" 2>&1 &
    OLLAMA_PID=$!
    OLLAMA_CMD=("$OLLAMA_EXE")
    wait_for_url "http://localhost:11435"
}

# ─── Helper: start llama.cpp server ──────────────────────────────────────────
start_llamacpp() {
    download_gguf
    # Only download portable binary if system llama-server isn't available
    if [[ "$LLAMA_SERVER" == "$BIN_DIR/llama-server" ]]; then
        download_llamacpp
    fi
    
    echo "🚀 Launching llama.cpp server on port 8080..."
    "$LLAMA_SERVER" \
        -m "$GGUF_PATH" \
        -c 3072 \
        --threads 4 \
        --threads-batch 4 \
        --batch-size 128 \
        --port 8080 \
        --host 127.0.0.1 \
        > "$BIN_DIR/llama.log" 2>&1 &
    LLAMA_PID=$!
    wait_for_url "http://localhost:8080/health"
}

# ─── Boot ────────────────────────────────────────────────────────────────────
start_llamacpp
trap "kill $LLAMA_PID 2>/dev/null; echo '🔌 Matus engine stopped.'" EXIT

echo "✅ Launching Matus..."
python3 "$REPO_DIR/main.py"
