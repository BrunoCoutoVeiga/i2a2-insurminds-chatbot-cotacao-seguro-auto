# Backend FastAPI do InsurMind, otimizado pra HuggingFace Spaces (Docker SDK).
#
# Free tier do HF Spaces: 16GB RAM (vs 512MB do Render free) — sobra de
# memória pro e5-base em fp16 + tudo o resto. Mantém o stack original
# (Anthropic API, ChromaDB, sentence-transformers) sem refator.
#
# Build:
#   - Instala pacote + deps com pip
#   - Roda scripts/ingest_kb.py uma vez pra gerar o índice .chroma (~312 chunks)
#
# Runtime:
#   - uvicorn ouvindo na porta 7860 (default do HF Spaces, configurável via README)

FROM python:3.12-slim

# HF Spaces exige usuário não-root rodando como UID 1000.
# Sem isso, o container falha ao subir com "permission denied".
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app

# Adiciona o bin do pip --user no PATH pra `uvicorn` ser encontrado.
ENV PATH="/home/user/.local/bin:$PATH"

# Stdout/stderr sem buffer — logs aparecem em tempo real no painel do Space.
ENV PYTHONUNBUFFERED=1

# Cache do HuggingFace dentro do home do user (writable).
ENV HF_HOME=/home/user/.cache/huggingface

# === Etapa 1: instalar dependências ===
# Copia primeiro só pyproject.toml + src/ pra que o pip layer fique cacheado
# enquanto data/ e scripts/ mudam (build incremental mais rápido em re-deploys).
COPY --chown=user pyproject.toml ./
COPY --chown=user src/ ./src/

RUN pip install --user --no-cache-dir --upgrade pip && \
    pip install --user --no-cache-dir -e .

# === Etapa 2: copiar dados e gerar índice ChromaDB ===
COPY --chown=user data/ ./data/
COPY --chown=user scripts/ ./scripts/

# Gera o .chroma/ no container (downloads o modelo e5-base + embed dos 312 chunks).
# Demora ~3-5min na primeira build; subsequentes usam cache de layer Docker.
RUN python scripts/ingest_kb.py

# === Etapa 3: configurar uvicorn ===
# HF Spaces espera o app escutando na porta 7860 por convenção.
EXPOSE 7860

CMD ["python", "-m", "uvicorn", "insurmind.api:app", \
     "--host", "0.0.0.0", \
     "--port", "7860", \
     "--log-level", "info"]
