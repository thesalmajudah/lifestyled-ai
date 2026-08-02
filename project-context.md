# PROJECT_CONTEXT — LifeStyled

## Project
LifeStyled — Dress for the Life You Live  
LLM Zoomcamp 2026 Capstone Project

## Goal
Build an end-to-end RAG fashion assistant that recommends products based on a user’s style, lifestyle, budget, climate, and occasion.

## Why this project
Users struggle to find clothing that fits their daily life and preferences. LifeStyled personalizes recommendations with explainable reasoning.

## Scope (MVP)
- User onboarding quiz (10-15 questions)
- Product catalog ingestion and indexing
- Retrieval (vector or hybrid BM25 + vector)
- Profile-aware ranking
- LLM-generated recommendation explanations
- Streamlit interface
- Feedback collection (+1/-1)
- Monitoring dashboard with core charts

## Out of Scope (for MVP)
- Multi-user auth
- Real-time web scraping
- Advanced long-term memory personalization
- Complex agent workflows

## Preferred Stack
- Python
- Streamlit
- scikit-learn (TF-IDF vectors)
- ChromaDB or FAISS
- rank-bm25 (if hybrid retrieval)
- SQLite
- LLM provider: Groq/OpenAI/Ollama

## Data Plan
- Product catalog CSV/JSON with fields:
  - product_id, title, category, brand, price
  - colors, sizes, style_tags, lifestyle_tags
  - climate_tags, occasion_tags, description, stock_status
- Optional support docs:
  - shipping policy, return policy, size guide, care guide

## Retrieval + Ranking Plan
1. Retrieve candidates from catalog
2. Apply metadata filters (budget, size, availability)
3. Compute profile match score:
   - style + lifestyle + climate + occasion + price fit
4. Return top 5 with explanation

## Evaluation Plan
### Retrieval Evaluation
- Compare:
  - vector-only
  - hybrid (BM25 + vector)
- Use a validation set of sample user queries
- Metric: relevance@k / hit-rate@k (simple and explainable)

### LLM Evaluation
- Compare Prompt A vs Prompt B
- Judge on:
  - relevance
  - groundedness
  - personalization quality
  - clarity

## Monitoring Plan
Track and store:
- timestamp
- user query
- profile summary
- retrieved item ids
- response text
- response time
- token usage/cost (if available)
- user feedback score (+1/-1)

Dashboard charts (target >=5):
1. Requests over time
2. Avg response time over time
3. Feedback trend
4. Top categories requested
5. Budget band distribution in queries
6. Optional: cost over time

## Reproducibility Plan
- Pinned dependencies
- .env.example
- One-command setup/run instructions
- Optional Dockerfile/docker-compose

## Current Status
- Project scaffold completed (app, src, scripts, data, logs)
- Seed fashion catalog added at data/raw/products_seed.csv
- Ingestion and baseline retrieval implemented (vector + hybrid)
- Streamlit app implemented with feedback logging
- Retrieval evaluation artifacts added (validation queries + report scripts)
- Groq explanation layer added with Prompt A/B
- Streamlit monitoring dashboard page added
- uv dependency workflow enabled (pyproject + uv lock)
- Dockerfile and docker-compose added
- Prompt variant scoring script added
- Prompt A/B manual scoring completed
- Default prompt selected: A (tie-break by personalization + groundedness)
- Retrieval tuning validated: hybrid relevance@5 improved to 0.5347 (hit-rate@5 remains 1.0)

## Next 3 Tasks
1. Capture app screenshots and add reviewer walkthrough to README
2. Add optional cost tracking field/chart if token usage is available
3. Evaluate re-ranking and query rewriting for best-practices points

## Implementation Steps
1. Foundation: scaffold, config, and starter dataset
2. Retrieval core: ingestion, indexing, and ranking baseline
3. UI baseline: recommendation page and feedback capture
4. Evaluation layer: validation set + retrieval metrics reporting
5. LLM layer: Groq explanations with Prompt A/B comparison
6. Monitoring: Streamlit dashboard with 5 required charts
7. Reproducibility: uv dependency management, env template, dockerization
8. Finalization: prompt choice decision + documentation polish
9. Submission prep: screenshots, final QA, and rubric pass