# =============================================================================
# Caculinha BI Agent Platform - Dockerfile
# Multi-stage build para ambiente de produção
# =============================================================================

# -----------------------------------------------------------------------------
# STAGE 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar apenas requirements primeiro (cache de camadas)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Precarregar o modelo de embeddings no build para evitar fallback no primeiro request
COPY . backend/
ENV PYTHONPATH=/app \
    RAG_EMBEDDING_LOCAL_FILES_ONLY=false
RUN python backend/scripts/maintenance/preload_embedding_model.py --allow-download || true

# -----------------------------------------------------------------------------
# STAGE 2: Production
# -----------------------------------------------------------------------------
FROM python:3.11-slim as production

WORKDIR /app

# Criar usuário não-root
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

# Copiar virtual environment do builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar código da aplicação dentro do diretório backend
COPY --chown=appuser:appuser . backend/
COPY --from=builder /app/backend/data/runtime/embedding_models /app/backend/data/runtime/embedding_models

# Variáveis de ambiente padrão
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    PORT=8000 \
    PYTHONPATH=/app \
    RAG_EMBEDDING_LOCAL_FILES_ONLY=true \
    RAG_EMBEDDING_PRELOAD_ON_STARTUP=true

# Expor porta
EXPOSE 8000

# Mudar para usuário não-root
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando padrão
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

# -----------------------------------------------------------------------------
# STAGE 3: Development (opcional)
# -----------------------------------------------------------------------------
FROM production as development

# Mudar para root para instalar deps de dev
USER root

# Instalar dependências de desenvolvimento
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    httpx \
    black \
    isort \
    mypy

# Mudar de volta para usuário não-root
USER appuser

# Comando para desenvolvimento com hot-reload
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "backend", "--reload-include", "*.py", "--reload-include", ".env"]
