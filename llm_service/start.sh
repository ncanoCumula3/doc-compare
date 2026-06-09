#!/usr/bin/env bash
# Start Ollama, ensure the model is present, then run the Python access layer.
set -e

MODEL="${LLM_MODEL:-qwen3:4b}"

# Memory hygiene for small CPU instances: keep one model resident (avoid reload
# churn), serialize requests, cap loaded models. Reduces peak RAM / OOM risk.
export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:--1}"
export OLLAMA_NUM_PARALLEL="${OLLAMA_NUM_PARALLEL:-1}"
export OLLAMA_MAX_LOADED_MODELS="${OLLAMA_MAX_LOADED_MODELS:-1}"

# Start the Ollama server in the background.
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to accept connections.
echo "waiting for ollama..."
for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

# Pull the model in the BACKGROUND if not already present. This lets llm_api bind
# the port immediately so Render's health check passes; /analyze just errors until
# the pull finishes (a minute or two on first boot without a persistent disk).
if ! ollama list | grep -q "${MODEL%%:*}"; then
  echo "pulling $MODEL in background ..."
  ( ollama pull "$MODEL" && echo "model $MODEL ready" ) &
fi

# Hand off to the Python access layer (foreground = container's main process).
exec python3 /app/llm_api.py
