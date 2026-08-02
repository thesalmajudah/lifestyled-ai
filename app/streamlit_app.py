import json
import time
from pathlib import Path
import os

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

load_dotenv(ROOT_DIR / ".env")

# In Streamlit Cloud, users often configure keys in Secrets instead of .env.
try:
    if not os.getenv("GROQ_API_KEY") and "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = str(st.secrets["GROQ_API_KEY"])
    if not os.getenv("GROQ_MODEL") and "GROQ_MODEL" in st.secrets:
        os.environ["GROQ_MODEL"] = str(st.secrets["GROQ_MODEL"])
except Exception:
    # Ignore secrets access errors and fall back to env/.env behavior.
    pass

from lifestyled.config import EVENT_LOG_PATH
from lifestyled.agentic import AgenticRecommender
from lifestyled import explanations as explanations_module
from lifestyled.ingestion import build_index
from lifestyled.models import UserProfile
from lifestyled.retrieval import ProductRetriever

generate_explanation = getattr(explanations_module, "generate_explanation", None)
generate_style_advice = getattr(explanations_module, "generate_style_advice", None)
generate_match_advice = getattr(explanations_module, "generate_match_advice", None)

DEFAULT_SEARCH_MODE = "hybrid"
DEFAULT_AGENTIC_LOOP = True
DEFAULT_ITEM_EXPLANATIONS = False
DEFAULT_PROMPT_VARIANT = "A"

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

            h2.shopping-title {
                color: #111111 !important;
                font-size: 1rem !important;
                font-weight: 400 !important;
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
                position: sticky;
                top: 0;
                height: 100vh;
                overflow-y: auto;
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

            /* Hide the static min/max labels under the budget slider; keep handle values visible */
            .stSlider [data-testid="stSliderTickBar"] {
                display: none !important;
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
    st.session_state.last_mode = DEFAULT_SEARCH_MODE
if "last_latency_ms" not in st.session_state:
    st.session_state.last_latency_ms = None
if "last_prompt_variant" not in st.session_state:
    st.session_state.last_prompt_variant = DEFAULT_PROMPT_VARIANT
if "last_llm_enabled" not in st.session_state:
    st.session_state.last_llm_enabled = DEFAULT_ITEM_EXPLANATIONS
if "last_agentic_enabled" not in st.session_state:
    st.session_state.last_agentic_enabled = DEFAULT_AGENTIC_LOOP
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
if "trigger_search" not in st.session_state:
    st.session_state.trigger_search = False
if "queued_query" not in st.session_state:
    st.session_state.queued_query = ""
if "profile_style_tags" not in st.session_state:
    st.session_state.profile_style_tags = []
if "profile_lifestyle_tags" not in st.session_state:
    st.session_state.profile_lifestyle_tags = []
if "profile_climate_tags" not in st.session_state:
    st.session_state.profile_climate_tags = []
if "profile_occasion_tags" not in st.session_state:
    st.session_state.profile_occasion_tags = []
if "profile_budget_range" not in st.session_state:
    st.session_state.profile_budget_range = (5, 600)
if "profile_size" not in st.session_state:
    st.session_state.profile_size = None
if "reset_requested" not in st.session_state:
    st.session_state.reset_requested = False
if "last_no_match_advice" not in st.session_state:
    st.session_state.last_no_match_advice = ""
if "last_no_match_advice_error" not in st.session_state:
    st.session_state.last_no_match_advice_error = ""
if "last_match_advice" not in st.session_state:
    st.session_state.last_match_advice = ""
if "last_match_advice_error" not in st.session_state:
    st.session_state.last_match_advice_error = ""

if st.session_state.reset_requested:
    st.session_state.last_results = []
    st.session_state.last_query = ""
    st.session_state.last_profile = None
    st.session_state.last_mode = DEFAULT_SEARCH_MODE
    st.session_state.last_latency_ms = None
    st.session_state.last_prompt_variant = DEFAULT_PROMPT_VARIANT
    st.session_state.last_llm_enabled = DEFAULT_ITEM_EXPLANATIONS
    st.session_state.last_agentic_enabled = DEFAULT_AGENTIC_LOOP
    st.session_state.last_agent_steps = []
    st.session_state.last_agent_stop_reason = ""
    st.session_state.last_agent_quality = None
    st.session_state.effective_query = ""
    st.session_state.query_draft = ""
    st.session_state.trigger_search = False
    st.session_state.queued_query = ""
    st.session_state.profile_style_tags = []
    st.session_state.profile_lifestyle_tags = []
    st.session_state.profile_climate_tags = []
    st.session_state.profile_occasion_tags = []
    st.session_state.profile_budget_range = (5, 600)
    st.session_state.profile_size = None
    st.session_state.pop("feedback_choice", None)
    st.session_state.last_no_match_advice = ""
    st.session_state.last_no_match_advice_error = ""
    st.session_state.last_match_advice = ""
    st.session_state.last_match_advice_error = ""
    st.session_state.reset_requested = False

landing_prompts = [
    "I need a minimal office outfit for mild weather",
    "Looking for vacation swimwear for warm weather around 130",
    "Need polished workwear for office commute",
]


def queue_search() -> None:
    st.session_state.trigger_search = bool(st.session_state.query_draft.strip())


def clear_conversation() -> None:
    st.session_state.reset_requested = True


def llm_advice_error_message(error_text: str, context: str) -> str:
    message = (error_text or "").lower()
    if (
        "groq_api_key is not set" in message
        or "api key" in message
        or "authentication" in message
        or "unauthorized" in message
        or "forbidden" in message
        or "401" in message
        or "403" in message
    ):
        return f"LLM stylist advice unavailable for {context}. Configure GROQ_API_KEY in Streamlit Cloud Secrets."
    if "429" in message or "rate" in message or "quota" in message or "limit" in message:
        return "LLM stylist advice is rate-limited right now. Please retry in a few seconds."
    if "model" in message or "not found" in message or "does not exist" in message or "unsupported" in message:
        return "LLM stylist advice model is unavailable in this environment. Verify GROQ_MODEL in Secrets."
    if (
        "timeout" in message
        or "timed out" in message
        or "connection" in message
        or "network" in message
        or "502" in message
        or "503" in message
        or "504" in message
    ):
        return "LLM stylist advice is temporarily unreachable due to a network/provider issue. Please retry."
    return f"LLM stylist advice is temporarily unavailable for {context}."


def generate_runtime_style_advice(query: str, profile: UserProfile, items=None) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    item_text = ""
    if items:
        top = [f"{it.title} ({it.category}, ${it.price:.2f})" for it in items[:5]]
        item_text = "Matched items: " + "; ".join(top)

    prompt = (
        "You are a personal stylist giving practical outfit advice. "
        "Provide one short recommendation sentence, then 3 bullets, then 1 optional swap. "
        "Be concise and grounded in the user profile. "
        f"Query: {query}\n"
        f"Style tags: {profile.style_tags}\n"
        f"Lifestyle tags: {profile.lifestyle_tags}\n"
        f"Climate tags: {profile.climate_tags}\n"
        f"Occasion tags: {profile.occasion_tags}\n"
        f"Budget: {profile.budget_min}-{profile.budget_max}\n"
        f"Size: {profile.size}\n"
        f"{item_text}"
    )

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Be concise, practical, and fashion-aware."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
    )
    return (completion.choices[0].message.content or "").strip()

with st.sidebar:
    st.header("Your Profile")
    style_tags = st.multiselect(
        "Aesthetic",
        ["minimal", "casual", "smart-casual", "classic", "elegant", "sport", "outdoor", "street", "cozy"],
        key="profile_style_tags",
    )
    lifestyle_tags = st.multiselect(
        "Lifestyle",
        ["office", "remote-work", "commute", "travel", "weekend", "gym", "events", "errands", "vacation", "hiking"],
        key="profile_lifestyle_tags",
    )
    climate_tags = st.multiselect(
        "Climate",
        ["warm", "mild", "cool", "cold", "rainy", "windy", "all-season"],
        key="profile_climate_tags",
    )
    occasion_tags = st.multiselect(
        "Occasion",
        ["work", "casual", "formal", "dinner", "active", "travel", "brunch", "special occasion"],
        key="profile_occasion_tags",
    )
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
        key="profile_size",
        index=None,
        placeholder="Choose size",
    )
    budget_min, budget_max = st.slider("Budget range", 5, 600, key="profile_budget_range")
    st.divider()
    st.button(
        "Clear conversation",
        key="clear_conversation_btn",
        help="Reset query, profile, and results",
        use_container_width=True,
        on_click=clear_conversation,
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

    st.session_state.last_no_match_advice = ""
    st.session_state.last_no_match_advice_error = ""
    st.session_state.last_match_advice = ""
    st.session_state.last_match_advice_error = ""
    if run_results:
        try:
            if generate_match_advice is not None:
                st.session_state.last_match_advice = generate_match_advice(
                    query=query,
                    profile=profile,
                    items=run_results,
                )
            elif generate_style_advice is not None:
                st.session_state.last_match_advice = generate_style_advice(query=query, profile=profile)
            else:
                st.session_state.last_match_advice = generate_runtime_style_advice(query=query, profile=profile, items=run_results)
        except Exception as exc:
            # Fall back to a simpler LLM advice prompt if matched-item advice fails.
            try:
                if generate_style_advice is not None:
                    st.session_state.last_match_advice = generate_style_advice(query=query, profile=profile)
                else:
                    st.session_state.last_match_advice = generate_runtime_style_advice(query=query, profile=profile, items=run_results)
                st.session_state.last_match_advice_error = ""
            except Exception as fallback_exc:
                st.session_state.last_match_advice_error = str(fallback_exc or exc)
    else:
        try:
            if generate_style_advice is not None:
                st.session_state.last_no_match_advice = generate_style_advice(query=query, profile=profile)
            else:
                st.session_state.last_no_match_advice = generate_runtime_style_advice(query=query, profile=profile)
        except Exception as exc:
            st.session_state.last_no_match_advice_error = str(exc)

    st.rerun()

results = st.session_state.last_results
profile = st.session_state.last_profile

if not results:
    st.markdown("<h2 class='shopping-title' style='text-align:center; margin-top: 1.8rem;'>What are you looking for today?</h2>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 1.6, 1])
    with center_col:
        query_col, submit_col = st.columns([12, 1])
        with query_col:
            st.text_input("What are you looking for today?", key="query_draft", label_visibility="collapsed", on_change=queue_search)
        with submit_col:
            if st.button(
                "↑",
                key="submit_query_top",
                help="Submit query",
                disabled=not bool(st.session_state.query_draft.strip()),
            ):
                st.session_state.trigger_search = True
                st.rerun()
        for idx, prompt in enumerate(landing_prompts):
            if st.button(prompt, key=f"landing_prompt_{idx}"):
                st.session_state.queued_query = prompt
                st.session_state.trigger_search = True
                st.rerun()

if results and profile:
    if not profile.size:
        st.caption("Size is optional. Select a size in the sidebar to filter results by fit availability.")

    if st.session_state.last_match_advice:
        st.markdown("### Stylist advice")
        st.caption("LLM-generated guidance based on your query, profile, and top matched items.")
        st.write(st.session_state.last_match_advice)
        st.divider()
    elif st.session_state.last_match_advice_error:
        st.info(llm_advice_error_message(st.session_state.last_match_advice_error, "matched results"))
        with st.expander("Advice error details"):
            st.code(st.session_state.last_match_advice_error)

    allow_llm = (
        st.session_state.last_llm_enabled
        and bool(os.getenv("GROQ_API_KEY", "").strip())
        and generate_explanation is not None
    )
    if st.session_state.last_llm_enabled and not allow_llm:
        if generate_explanation is None:
            st.info("LLM explanation helper unavailable in this deployment version. Showing retrieval reasons only.")
        else:
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
    if st.session_state.last_no_match_advice:
        st.markdown("### Stylist advice")
        st.caption("General guidance based on your query and profile when exact catalog matches are unavailable.")
        st.write(st.session_state.last_no_match_advice)
    elif st.session_state.last_no_match_advice_error:
        st.info(llm_advice_error_message(st.session_state.last_no_match_advice_error, "no-match fallback"))
        with st.expander("Advice error details"):
            st.code(st.session_state.last_no_match_advice_error)

if results:
    st.divider()
    st.markdown("### Continue searching")
    query_col, submit_col = st.columns([12, 1])
    with query_col:
        st.text_input("What are you shopping for today?", key="query_draft", on_change=queue_search)
    with submit_col:
        if st.button(
            "↑",
            key="submit_query_bottom",
            help="Submit query",
            disabled=not bool(st.session_state.query_draft.strip()),
        ):
            st.session_state.trigger_search = True
            st.rerun()

if st.session_state.trigger_search:
    st.session_state.trigger_search = False
    query_to_run = st.session_state.queued_query or st.session_state.query_draft
    st.session_state.queued_query = ""
    run_recommendations(
        query=query_to_run,
        mode=DEFAULT_SEARCH_MODE,
        use_agentic_loop=DEFAULT_AGENTIC_LOOP,
        use_llm_explanations=DEFAULT_ITEM_EXPLANATIONS,
        prompt_variant=DEFAULT_PROMPT_VARIANT,
    )
