# LifeStyled AI

LifeStyled - Dress for the Life You Live  
LLM Zoomcamp 2026 Capstone Project

## Problem Description

Finding clothing that fits real-life constraints is harder than basic search can handle. People need recommendations that account for:

- personal style
- lifestyle (office, commute, travel, weekend)
- climate
- occasion
- budget
- size and stock

LifeStyled is a profile-aware fashion assistant that retrieves relevant products and explains why each recommendation fits the user.

## Current Project Status

Implemented so far:

- starter product dataset
- ingestion pipeline to vector index (ChromaDB)
- lexical retrieval state export for BM25
- baseline retrieval engine with:
	- vector retrieval
	- hybrid retrieval (BM25 + vector)
	- profile-aware scoring
	- metadata filters (budget, size, stock)
- Streamlit interface
- feedback logging to JSONL
- retrieval validation dataset and evaluation script
- Groq-based LLM explanation layer (Prompt A/B)
- prompt variant evaluation runner
- Streamlit monitoring dashboard page with 5 core charts
- uv-based dependency management configured

In progress:

- prompt variant scoring (A vs B) on evaluation dimensions
- docker-compose packaging

## Step-by-Step Implementation Path

1. Foundation setup
- project scaffold
- config and models
- seed dataset

2. Retrieval baseline
- ingestion to Chroma using TF-IDF vectors
- BM25 state generation
- vector and hybrid search
- profile-aware filtering/ranking

3. MVP interface
- Streamlit recommendation UI
- user profile controls
- feedback logging

4. Evaluation artifacts
- validation query set
- retrieval metrics script and reports

5. Explanation layer
- Groq as default provider
- Prompt A/B support
- prompt output generation script

6. Monitoring
- dedicated Streamlit monitoring page
- five core rubric charts

7. Reproducibility
- uv-managed dependencies and lockfile
- env template
- docker-compose (next)

## Repository Structure

```text
.
├── app/
│   └── streamlit_app.py
│   └── pages/
│       └── 01_monitoring.py
├── data/
│   ├── eval/
│   │   └── validation_queries.json
│   ├── raw/
│   │   └── products_seed.csv
│   └── processed/
├── logs/
├── scripts/
│   └── build_index.py
│   └── evaluate_retrieval.py
├── reports/
├── src/
│   └── lifestyled/
│       ├── __init__.py
│       ├── config.py
│       ├── explanations.py
│       ├── ingestion.py
│       ├── models.py
│       └── retrieval.py
├── .env.example
├── requirements.txt
└── README.md
```

## Data

Starter dataset: `data/raw/products_seed.csv`

Columns:

- product_id
- title
- category
- brand
- price
- colors
- sizes
- style_tags
- lifestyle_tags
- climate_tags
- occasion_tags
- description
- stock_status

This dataset is a clean seed subset for MVP development and evaluation.

## Retrieval Flow

1. Ingest product catalog and build document text per product.
2. Generate TF-IDF vectors and store in ChromaDB.
3. Build BM25 corpus state for lexical matching.
4. At query time:
	 - run vector retrieval
	 - optionally run BM25 (hybrid mode)
	 - apply hard filters (budget, size, stock)
	 - compute profile match score
	 - return top-k ranked items with reasons

## Evaluation Plan

### Retrieval Evaluation

Compare:

- vector-only
- hybrid (BM25 + vector)

Metrics:

- hit-rate@k
- relevance@k

Use a validation set of user-style shopping queries.

Artifacts:

- validation set: data/eval/validation_queries.json
- evaluation runner: scripts/evaluate_retrieval.py
- generated reports:
	- reports/retrieval_eval.json
	- reports/retrieval_eval.md

### LLM Evaluation

Compare Prompt A vs Prompt B for generated explanations.

Judging dimensions:

- relevance
- groundedness in retrieved products
- personalization quality
- clarity

## Interface

Current interface: Streamlit app with:

- profile controls in sidebar
- query input
- retrieval mode toggle (hybrid/vector)
- top recommendations with reasons
- explicit feedback capture (+1 / -1)

## Monitoring

Feedback and request events are logged to `logs/events.jsonl`.

Logged fields include:

- timestamp
- query
- profile summary
- retrieval mode
- result ids
- response time
- feedback

Planned dashboard charts (>=5):

- [x] requests over time
- [x] avg response time over time
- [x] feedback trend
- [x] top categories requested
- [x] budget band distribution
- [ ] optional cost trend

Monitoring page:

- App includes a dedicated Streamlit page at app/pages/01_monitoring.py.
- It reads logs/events.jsonl and renders the charts above.

## Reproducibility

### 1) Install dependencies with uv

```bash
uv sync
```

### 2) Build index

```bash
uv run env PYTHONPATH=src python scripts/build_index.py
```

### 3) Run app

```bash
uv run env PYTHONPATH=src streamlit run app/streamlit_app.py
```

### 4) Run retrieval evaluation

```bash
uv run env PYTHONPATH=src python scripts/evaluate_retrieval.py
```

### 5) Environment variables

Copy .env.example to .env and fill values as needed.

### 6) Prompt A/B output generation

```bash
uv run env PYTHONPATH=src python scripts/evaluate_prompt_variants.py
```

## Technology Choices

- Python for implementation
- Streamlit for UI
- scikit-learn TF-IDF vectors for CPU-safe embeddings
- ChromaDB for vector storage
- rank-bm25 for lexical retrieval
- Groq for explanation generation
- JSONL logging for monitoring events

## Evaluation Criteria Mapping (Zoomcamp)

- Problem description: this README section "Problem Description"
- Retrieval flow: section "Retrieval Flow"
- Retrieval evaluation: section "Evaluation Plan / Retrieval Evaluation" (implemented; reports in reports/)
- LLM evaluation: section "Evaluation Plan / LLM Evaluation" (in progress)
- Interface: Streamlit app
- Ingestion pipeline: script-based ingestion baseline implemented
- Monitoring: event logging implemented, dashboard in progress
- Containerization: planned
- Reproducibility: setup and run commands included

Best practices goals:

- [x] Hybrid retrieval evaluated
- [ ] Re-ranking iteration planned
- [ ] Query rewriting iteration planned

### Prompt Variant Artifacts

- prompt variant runner: scripts/evaluate_prompt_variants.py
- generated output file: reports/prompt_variant_outputs.json

Run prompt variant output generation:

```bash
uv run env PYTHONPATH=src python scripts/evaluate_prompt_variants.py
```

Notes:

- Default provider is Groq.
- Set GROQ_API_KEY in local .env (never commit real keys).
- Streamlit includes a toggle for LLM explanations and a Prompt A/B selector.

## Notes

- The Zoomcamp FAQ dataset used in coursework is not used in this project.
- This is attempt-ready scaffolding and will be iterated with stronger evaluation, monitoring, and packaging.
