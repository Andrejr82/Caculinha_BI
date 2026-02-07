# Dockerfile — Caculinha BI Enterprise
# Multi-stage build para imagem otimizada

# ==========================================
# STAGE 1: Builder
# ==========================================
FROM python:3.11-slim as builder

WORKDIR /app

# Instala dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================
# STAGE 2: Runtime
# ==========================================
FROM python:3.11-slim as runtime

WORKDIR /app

# Cria usuário não-root
RUN useradd --create-home --shell /bin/bash appuser

# Copia dependências do builder
COPY --from=builder /root/.local /home/appuser/.local

# Garante que scripts estão no PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Copia código da aplicação
COPY backend/ ./backend/
COPY backend/.env.example ./backend/.env

# Cria diretórios de dados
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Muda para usuário não-root
USER appuser

# Expõe porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Comando de inicialização
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
