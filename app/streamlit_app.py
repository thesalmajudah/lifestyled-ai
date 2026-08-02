import json
import time
from pathlib import Path
import os

import streamlit as st
from dotenv import load_dotenv

import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

load_dotenv(ROOT_DIR / ".env")

from lifestyled.config import EVENT_LOG_PATH
from lifestyled.agentic import AgenticRecommender
from lifestyled.explanations import generate_explanation
from lifestyled.ingestion import build_index
from lifestyled.models import UserProfile
from lifestyled.retrieval import ProductRetriever

st.set_page_config(page_title="LifeStyled", page_icon="👗", layout="wide")

st.markdown(
        """
        <style>
            :root {
                --ls-pink: #e75480;
                --ls-purple: #a05ac2;
                --ls-pink-soft: #fff1f6;
                --ls-ink: #2f2f3d;
                --ls-action: #f0629b;
            }

            .brand-title {
                font-size: 3rem;
                font-weight: 800;
                color: var(--ls-ink);
                margin-bottom: 0.1rem;
                line-height: 1.1;
            }

            .brand-tagline {
                font-size: 1.65rem;
                color: var(--ls-pink);
                margin-top: 0;
                margin-bottom: 0.75rem;
                text-align: left;
            }

            h2, h3 {
                color: var(--ls-pink) !important;
            }

            .brand-divider {
                height: 4px;
                border: 0;
                border-radius: 999px;
                background: linear-gradient(90deg, var(--ls-pink), #ff9eb7);
                margin-top: 0.25rem;
                margin-bottom: 1rem;
            }

            section.main [data-testid="stTextInput"] {
                background: linear-gradient(120deg, #fff7fa, #fff1f6);
                border: 1px solid #ffd5e3;
                border-radius: 14px;
                padding: 0.55rem 0.7rem 0.25rem 0.7rem;
                margin-bottom: 0.9rem;
            }

            section.main [data-testid="stTextInput"] input {
                background: #ffffff !important;
            }

            .result-card {
                background: #ffffff;
                border: 1px solid #f4d0dc;
                border-left: 5px solid var(--ls-pink);
                border-radius: 12px;
                padding: 0.9rem 1rem;
                margin-bottom: 0.75rem;
            }

            .stButton > button {
                background: var(--ls-action);
                color: white !important;
                border: none;
            }

            .stButton > button:hover {
                filter: brightness(1.03);
            }

            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #fff8fb, #fff3f8);
            }

            section[data-testid="stSidebar"] h1,
            section[data-testid="stSidebar"] h2,
            section[data-testid="stSidebar"] h3,
            section[data-testid="stSidebar"] label,
            section[data-testid="stSidebar"] p {
                color: #c7436f !important;
            }

            section[data-testid="stSidebar"] [data-baseweb="tag"] {
                background-color: #e75480 !important;
                border-color: #e75480 !important;
                color: #ffffff !important;
            }

            section[data-testid="stSidebar"] [data-baseweb="select"] > div,
            section[data-testid="stSidebar"] [data-baseweb="input"] > div,
            section[data-testid="stSidebar"] .stTextInput input,
            section[data-testid="stSidebar"] .stNumberInput input {
                border-color: #e75480 !important;
                box-shadow: 0 0 0 1px #e75480 inset !important;
            }

            section[data-testid="stSidebar"] [role="radiogroup"] label,
            section[data-testid="stSidebar"] [data-testid="stCheckbox"] label {
                color: #c7436f !important;
            }

            /* Force accent color for selected radio/checkbox options */
            input[type="radio"],
            input[type="checkbox"] {
                accent-color: var(--ls-action) !important;
            }

            [data-testid="stRadio"] [role="radiogroup"] input,
            [data-testid="stCheckbox"] input {
                accent-color: var(--ls-action) !important;
            }

            /* Slider colors */
            .stSlider [data-baseweb="slider"] div[role="slider"] {
                background-color: var(--ls-pink) !important;
                border-color: var(--ls-pink) !important;
            }

            .stSlider [data-baseweb="slider"] > div > div > div {
                background: linear-gradient(90deg, #e75480, #ff6f9b) !important;
            }

            .stSlider [data-baseweb="slider"] > div > div > div + div {
                background: #ffd5e3 !important;
            }

            .stSlider p,
            .stSlider span,
            .stNumberInput p,
            .stNumberInput span {
                color: #5d5267 !important;
            }

        </style>
        """,
        unsafe_allow_html=True,
)

st.markdown("<h1 class='brand-title' style='text-align:left;'>👗 LifeStyled</h1>", unsafe_allow_html=True)
st.markdown("<p class='brand-tagline'><strong><em>Dress for the Life You Live</em></strong></p>", unsafe_allow_html=True)
st.markdown("<hr class='brand-divider' />", unsafe_allow_html=True)

if "last_results" not in st.session_state:
    st.session_state.last_results = []
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "last_profile" not in st.session_state:
    st.session_state.last_profile = None
if "last_mode" not in st.session_state:
    st.session_state.last_mode = "hybrid"
if "last_latency_ms" not in st.session_state:
    st.session_state.last_latency_ms = None
if "last_prompt_variant" not in st.session_state:
    st.session_state.last_prompt_variant = "A"
if "last_llm_enabled" not in st.session_state:
    st.session_state.last_llm_enabled = False
if "last_agentic_enabled" not in st.session_state:
    st.session_state.last_agentic_enabled = True
if "last_agent_steps" not in st.session_state:
    st.session_state.last_agent_steps = []
if "last_agent_stop_reason" not in st.session_state:
    st.session_state.last_agent_stop_reason = ""
if "last_agent_quality" not in st.session_state:
    st.session_state.last_agent_quality = None
if "effective_query" not in st.session_state:
    st.session_state.effective_query = ""
if "query_draft" not in st.session_state:
    st.session_state.query_draft = ""
if "mode_pref" not in st.session_state:
    st.session_state.mode_pref = "hybrid"
if "agentic_pref" not in st.session_state:
    st.session_state.agentic_pref = True
if "llm_pref" not in st.session_state:
    st.session_state.llm_pref = False
if "prompt_pref" not in st.session_state:
    st.session_state.prompt_pref = "A"
if "trigger_search" not in st.session_state:
    st.session_state.trigger_search = False
if "queued_query" not in st.session_state:
    st.session_state.queued_query = ""

landing_prompts = [
    "I need a minimal office outfit for mild weather under 140",
    "Looking for vacation swimwear for warm weather around 130",
    "Need polished workwear for office commute around 150",
    "Need a premium tote or shoulder bag for office events",
]


def options_dropdown(label: str):
    if hasattr(st, "popover"):
        return st.popover(label)
    return st.expander(label, expanded=False)


def queue_search() -> None:
    st.session_state.trigger_search = True

with st.sidebar:
    st.header("Your Profile")
    style_tags = st.multiselect(
        "Aesthetic",
        ["minimal", "casual", "smart-casual", "classic", "elegant", "sport", "outdoor", "street", "cozy"],
        default=[],
    )
    lifestyle_tags = st.multiselect(
        "Lifestyle",
        ["office", "remote-work", "commute", "travel", "weekend", "gym", "events", "errands", "vacation", "hiking"],
        default=[],
    )
    climate_tags = st.multiselect(
        "Climate",
        ["warm", "mild", "cool", "cold", "rainy", "windy", "all-season"],
        default=[],
    )
    occasion_tags = st.multiselect(
        "Occasion",
        ["work", "casual", "formal", "dinner", "active", "travel", "brunch", "special occasion"],
        default=[],
    )
    budget_min, budget_max = st.slider("Budget range", 5, 600, (5, 600))
    size = st.selectbox(
        "Size",
        [
            "XS",
            "S",
            "M",
            "L",
            "XL",
            "30",
            "32",
            "34",
            "36",
            "26",
            "28",
            "7",
            "8",
            "9",
            "10",
            "11",
        ],
        index=None,
        placeholder="Choose size",
    )


def run_recommendations(
    query: str,
    mode: str,
    use_agentic_loop: bool,
    use_llm_explanations: bool,
    prompt_variant: str,
) -> None:
    if not query.strip():
        st.warning("Please tell us what you are shopping for before running recommendations.")
        return
    if size is None:
        st.warning("Please select your size for accurate recommendations.")
        return

    try:
        retriever = ProductRetriever()
    except FileNotFoundError:
        with st.spinner("Index missing. Building local index from catalog..."):
            try:
                build_index()
                retriever = ProductRetriever()
                st.info("Index built successfully. Running recommendations...")
            except Exception as exc:
                st.error(
                    "Index build failed. Ensure data/raw/products_seed.csv is present and dependencies are installed. "
                    f"Details: {exc}"
                )
                return

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
    if use_agentic_loop:
        orchestrator = AgenticRecommender(retriever)
        run_result = orchestrator.run(query=query, profile=profile, retrieval_mode=mode, k=5)
        run_results = run_result.results
        st.session_state.last_agent_steps = run_result.steps_as_dicts()
        st.session_state.last_agent_stop_reason = run_result.stop_reason
        st.session_state.last_agent_quality = run_result.quality_score
        st.session_state.effective_query = run_result.final_query
    else:
        run_results = retriever.search(query=query, profile=profile, retrieval_mode=mode)
        st.session_state.last_agent_steps = []
        st.session_state.last_agent_stop_reason = "direct_retrieval"
        st.session_state.last_agent_quality = None
        st.session_state.effective_query = query
    latency_ms = (time.perf_counter() - start) * 1000

    st.session_state.last_results = run_results
    st.session_state.last_query = query
    st.session_state.last_profile = profile
    st.session_state.last_mode = mode
    st.session_state.last_latency_ms = round(latency_ms, 2)
    st.session_state.last_prompt_variant = prompt_variant
    st.session_state.last_llm_enabled = use_llm_explanations
    st.session_state.last_agentic_enabled = use_agentic_loop
    st.rerun()

results = st.session_state.last_results
profile = st.session_state.last_profile

if not results:
    st.markdown("<h2 style='text-align:center; color:#1f2433 !important; margin-top: 1.8rem;'>What are you shopping for today?</h2>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 1.6, 1])
    with center_col:
        st.text_input("What are you shopping for today?", key="query_draft", label_visibility="collapsed", on_change=queue_search)
        if st.button("Submit", key="submit_query_top", disabled=not st.session_state.query_draft.strip()):
            st.session_state.trigger_search = True
            st.rerun()
        with options_dropdown("Tune recommendations"):
            st.radio(
                "Search mode",
                ["hybrid", "vector"],
                key="mode_pref",
                horizontal=True,
                help="Hybrid combines text and semantic matching. Vector uses semantic matching only.",
            )
            st.checkbox(
                "Use smarter search retry (beta)",
                key="agentic_pref",
                help="If first results look weak, the app refines your query once and reranks results.",
            )
            st.checkbox(
                "Add AI style explanations",
                key="llm_pref",
                help="Adds short AI-generated reasons for each recommendation.",
            )
            if st.session_state.llm_pref:
                st.selectbox(
                    "Explanation style",
                    ["A", "B"],
                    key="prompt_pref",
                    help="Style A is concise bullets. Style B is structured JSON-like reasoning.",
                )
            else:
                st.session_state.prompt_pref = "A"

        for idx, prompt in enumerate(landing_prompts):
            if st.button(prompt, key=f"landing_prompt_{idx}"):
                st.session_state.queued_query = prompt
                st.session_state.trigger_search = True
                st.rerun()

if results and profile:
    if st.session_state.last_agentic_enabled:
        st.caption(
            "Agentic loop: "
            f"stop_reason={st.session_state.last_agent_stop_reason}; "
            f"quality={st.session_state.last_agent_quality}; "
            f"effective_query={st.session_state.effective_query}"
        )
        with st.expander("Agent steps"):
            st.json(st.session_state.last_agent_steps)

    allow_llm = st.session_state.last_llm_enabled and bool(os.getenv("GROQ_API_KEY", "").strip())
    if st.session_state.last_llm_enabled and not allow_llm:
        st.info("GROQ_API_KEY missing. Showing retrieval reasons only.")

    for idx, item in enumerate(results, start=1):
        st.subheader(f"{idx}. {item.title} (${item.price:.2f})")
        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
        st.write(f"Brand: {item.brand} | Category: {item.category} | Score: {item.score}")
        st.write(f"Why: {item.reason}")
        st.markdown("</div>", unsafe_allow_html=True)

        if allow_llm:
            try:
                llm_text = generate_explanation(
                    query=st.session_state.last_query,
                    profile=profile,
                    item=item,
                    prompt_variant=st.session_state.last_prompt_variant,
                )
                st.write(f"AI explanation ({st.session_state.last_prompt_variant}):")
                st.write(llm_text)
            except Exception as exc:
                st.warning(f"AI explanation unavailable: {exc}")

    st.divider()
    feedback = st.radio("Was this helpful?", ["+1", "-1"], horizontal=True, key="feedback_choice")
    if st.button("Submit Feedback", key="submit_feedback"):
        EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "timestamp": time.time(),
            "query": st.session_state.last_query,
            "profile": {
                "style_tags": profile.style_tags,
                "lifestyle_tags": profile.lifestyle_tags,
                "climate_tags": profile.climate_tags,
                "occasion_tags": profile.occasion_tags,
                "budget_min": profile.budget_min,
                "budget_max": profile.budget_max,
                "size": profile.size,
            },
            "retrieval_mode": st.session_state.last_mode,
            "result_ids": [r.product_id for r in results],
            "response_time_ms": st.session_state.last_latency_ms,
            "feedback": int(feedback),
            "prompt_variant": st.session_state.last_prompt_variant,
            "llm_explanations_enabled": st.session_state.last_llm_enabled,
            "agentic_enabled": st.session_state.last_agentic_enabled,
            "agentic_stop_reason": st.session_state.last_agent_stop_reason,
            "agentic_quality": st.session_state.last_agent_quality,
            "effective_query": st.session_state.effective_query,
            "agent_steps": st.session_state.last_agent_steps,
        }
        with EVENT_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=True) + "\n")
        st.success("Feedback saved")
elif st.session_state.last_query:
    st.warning("No matching items found. Try widening budget, changing size, or adjusting tags.")

if results:
    st.divider()
    st.markdown("### Continue searching")
    st.text_input("What are you shopping for today?", key="query_draft", on_change=queue_search)
    if st.button("Submit", key="submit_query_bottom", disabled=not st.session_state.query_draft.strip()):
        st.session_state.trigger_search = True
        st.rerun()
    with options_dropdown("Tune recommendations"):
        st.radio(
            "Search mode",
            ["hybrid", "vector"],
            key="mode_pref",
            horizontal=True,
            help="Hybrid combines text and semantic matching. Vector uses semantic matching only.",
        )
        st.checkbox(
            "Use smarter search retry (beta)",
            key="agentic_pref",
            help="If first results look weak, the app refines your query once and reranks results.",
        )
        st.checkbox(
            "Add AI style explanations",
            key="llm_pref",
            help="Adds short AI-generated reasons for each recommendation.",
        )
        if st.session_state.llm_pref:
            st.selectbox(
                "Explanation style",
                ["A", "B"],
                key="prompt_pref",
                help="Style A is concise bullets. Style B is structured JSON-like reasoning.",
            )
        else:
            st.session_state.prompt_pref = "A"

if st.session_state.trigger_search:
    st.session_state.trigger_search = False
    query_to_run = st.session_state.queued_query or st.session_state.query_draft
    st.session_state.queued_query = ""
    run_recommendations(
        query=query_to_run,
        mode=st.session_state.mode_pref,
        use_agentic_loop=st.session_state.agentic_pref,
        use_llm_explanations=st.session_state.llm_pref,
        prompt_variant=st.session_state.prompt_pref,
    )
