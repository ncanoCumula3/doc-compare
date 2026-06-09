# Local LLM service: Ollama + Qwen3 4B + thin Python access layer.
FROM ollama/ollama:latest

# Ollama image is based on Ubuntu; add Python + curl for the wrapper and healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends python3 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY llm_api.py start.sh /app/
RUN chmod +x /app/start.sh

ENV LLM_MODEL=qwen3:4b
ENV OLLAMA_MODELS=/root/.ollama/models
# Render injects PORT; the wrapper listens on it.
ENV PORT=8000
EXPOSE 8000

# Override the base image's ENTRYPOINT (which is `ollama`) so our script runs.
ENTRYPOINT []
CMD ["/app/start.sh"]
