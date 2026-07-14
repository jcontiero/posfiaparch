# Etapa 1: builder — instala dependências de produção
FROM python:3.12-slim AS builder

WORKDIR /app

# Instala dependências de sistema necessárias para compilar pacotes (pg8000, bcrypt, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas o arquivo de dependências para aproveitar o cache de camadas
COPY pyproject.toml .

# Cria ambiente virtual e instala o projeto
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Etapa 2: imagem final enxuta
FROM python:3.12-slim

WORKDIR /app

# Cria usuário não-root para execução da aplicação
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copia o ambiente virtual da etapa builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app

# Copia o código-fonte da aplicação
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY alembic.ini ./

# Define permissões para o usuário não-root
RUN chown -R appuser:appgroup /app
USER appuser

# Expõe a porta padrão da aplicação
EXPOSE 8000

# Health check leve que não depende do banco
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# A aplicação inicia apenas o servidor UVicorn (sem DDL/seeds no startup)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
