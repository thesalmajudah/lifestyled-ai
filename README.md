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

In progress:

- retrieval evaluation script and metrics reporting
- LLM explanation layer (Prompt A vs Prompt B evaluation)
- monitoring dashboard with 5+ charts
- docker-compose packaging

## Repository Structure

```text
.
├── app/
│   └── streamlit_app.py
├── data/
│   ├── raw/
│   │   └── products_seed.csv
│   └── processed/
├── logs/
├── scripts/
│   └── build_index.py
├── src/
│   └── lifestyled/
│       ├── __init__.py
│       ├── config.py
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
2. Generate embeddings and store in ChromaDB.
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

- requests over time
- avg response time over time
- feedback trend
- top categories requested
- budget band distribution
- optional cost trend

## Reproducibility

### 1) Create and activate environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Build index

```bash
PYTHONPATH=src python scripts/build_index.py
```

### 3) Run app

```bash
PYTHONPATH=src streamlit run app/streamlit_app.py
```

### 4) Environment variables

Copy `.env.example` to `.env` and fill values as needed.

## Technology Choices

- Python for implementation
- Streamlit for UI
- sentence-transformers for embeddings
- ChromaDB for vector storage
- rank-bm25 for lexical retrieval
- JSONL logging for monitoring events

## Evaluation Criteria Mapping (Zoomcamp)

- Problem description: this README section "Problem Description"
- Retrieval flow: section "Retrieval Flow"
- Retrieval evaluation: section "Evaluation Plan / Retrieval Evaluation" (in progress)
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

## Notes

- The Zoomcamp FAQ dataset used in coursework is not used in this project.
- This is attempt-ready scaffolding and will be iterated with stronger evaluation, monitoring, and packaging.
