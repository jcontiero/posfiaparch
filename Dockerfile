FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ ./src/
COPY scripts/ ./scripts/

CMD ["sh", "-c", "python -c 'from src.shared.banco import Base, engine; import src.identidade.infraestrutura.modelos; import src.atendimento.infraestrutura.modelos; import src.catalogo.infraestrutura.modelos; import src.estoque.infraestrutura.modelos; Base.metadata.create_all(engine)' && python scripts/seed.py && python scripts/seed_mock.py && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
