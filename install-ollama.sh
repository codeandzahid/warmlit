#!/usr/bin/env bash
# Free local AI brain for Warmlit — NO API key, ever.
# Installs Ollama + a small model (~1 GB). Warmlit auto-detects it.
set -e
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi
ollama serve >/dev/null 2>&1 &
sleep 3
ollama pull qwen2.5:1.5b
echo "Done. Start Warmlit with ./run.sh — it will use the local model alone."
