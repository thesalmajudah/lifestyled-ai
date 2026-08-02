import json
import time
from pathlib import Path
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

load_dotenv(ROOT_DIR / ".env")

from lifestyled.config import EVENT_LOG_PATH
from lifestyled.explanations import generate_explanation
from lifestyled.models import UserProfile
from lifestyled.retrieval import ProductRetriever

st.set_page_config(page_title="LifeStyled", layout="wide")
st.title("LifeStyled - Dress for the Life You Live")

st.caption("Profile-aware fashion recommendations powered by retrieval + ranking")

with st.sidebar:
    st.header("Your Profile")
    style_tags = st.multiselect(
        "Style",
        ["minimal", "casual", "smart-casual", "classic", "elegant", "sport", "outdoor", "street", "cozy"],
        default=["minimal", "smart-casual"],
    )
    lifestyle_tags = st.multiselect(
        "Lifestyle",
        ["office", "remote-work", "commute", "travel", "weekend", "gym", "events", "errands", "vacation", "hiking"],
        default=["office", "commute"],
    )
    climate_tags = st.multiselect(
        "Climate",
        ["warm", "mild", "cool", "cold", "rainy", "windy", "all-season"],
        default=["mild"],
    )
    occasion_tags = st.multiselect(
        "Occasion",
        ["work", "casual", "formal", "dinner", "active", "travel", "brunch"],
        default=["work"],
    )
    budget_min, budget_max = st.slider("Budget range", 20, 250, (50, 140))
    size = st.selectbox("Size", ["XS", "S", "M", "L", "XL", "30", "32", "34", "36", "26", "28", "7", "8", "9", "10", "11"])

query = st.text_input("What are you shopping for today?", "I need an office outfit for mild weather under $140")
mode = st.radio("Retrieval mode", ["hybrid", "vector"], horizontal=True)
use_llm_explanations = st.checkbox("Use Groq LLM explanations", value=False)
prompt_variant = st.selectbox("Explanation prompt variant", ["A", "B"], index=0)

if st.button("Get Recommendations"):
    try:
        retriever = ProductRetriever()
    except FileNotFoundError:
        st.error("Index not found. Run: PYTHONPATH=src python scripts/build_index.py")
    else:
        profile = UserProfile(
            style_tags=style_tags,
            lifestyle_tags=lifestyle_tags,
            climate_tags=climate_tags,
            occasion_tags=occasion_tags,
            budget_min=float(budget_min),
            budget_max=float(budget_max),
            size=size,
        )

        start = time.perf_counter()
        results = retriever.search(query=query, profile=profile, retrieval_mode=mode)
        latency_ms = (time.perf_counter() - start) * 1000

        if not results:
            st.warning("No matching items found. Try widening budget, changing size, or adjusting tags.")
        else:
            allow_llm = use_llm_explanations and bool(os.getenv("GROQ_API_KEY", "").strip())
            if use_llm_explanations and not allow_llm:
                st.info("GROQ_API_KEY missing. Showing retrieval reasons only.")

            for idx, item in enumerate(results, start=1):
                st.subheader(f"{idx}. {item.title} (${item.price:.2f})")
                st.write(f"Brand: {item.brand} | Category: {item.category} | Score: {item.score}")
                st.write(f"Why: {item.reason}")

                if allow_llm:
                    try:
                        llm_text = generate_explanation(
                            query=query,
                            profile=profile,
                            item=item,
                            prompt_variant=prompt_variant,
                        )
                        st.write(f"LLM explanation ({prompt_variant}):")
                        st.write(llm_text)
                    except Exception as exc:
                        st.warning(f"LLM explanation unavailable: {exc}")

            st.divider()
            feedback = st.radio("Was this helpful?", ["+1", "-1"], horizontal=True)
            if st.button("Submit Feedback"):
                EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                event = {
                    "timestamp": time.time(),
                    "query": query,
                    "profile": {
                        "style_tags": style_tags,
                        "lifestyle_tags": lifestyle_tags,
                        "climate_tags": climate_tags,
                        "occasion_tags": occasion_tags,
                        "budget_min": budget_min,
                        "budget_max": budget_max,
                        "size": size,
                    },
                    "retrieval_mode": mode,
                    "result_ids": [r.product_id for r in results],
                    "response_time_ms": round(latency_ms, 2),
                    "feedback": int(feedback),
                    "prompt_variant": prompt_variant,
                    "llm_explanations_enabled": use_llm_explanations,
                }
                with EVENT_LOG_PATH.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(event, ensure_ascii=True) + "\n")
                st.success("Feedback saved")
