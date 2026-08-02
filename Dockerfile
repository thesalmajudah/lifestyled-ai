FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.12.1

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY app ./app
COPY scripts ./scripts
COPY data ./data

RUN uv sync --frozen

EXPOSE 8501

CMD ["bash", "-lc", "uv run env PYTHONPATH=src python scripts/build_index.py && uv run env PYTHONPATH=src streamlit run app/streamlit_app.py --server.address=0.0.0.0 --server.port=8501"]
