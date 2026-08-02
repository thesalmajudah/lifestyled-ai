import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
EVENT_LOG_PATH = ROOT_DIR / "logs" / "events.jsonl"
CATALOG_PATH = ROOT_DIR / "data" / "raw" / "products_seed.csv"

st.set_page_config(page_title="LifeStyled Monitoring", layout="wide")

PINK = "#e75480"

st.markdown(
        """
        <style>
            .monitor-title {
                color: #2f2f3d;
                font-weight: 800;
                margin-bottom: 0.2rem;
            }

            h2, h3 {
                color: #e75480 !important;
            }

            .monitor-divider {
                height: 4px;
                border: 0;
                border-radius: 999px;
                background: linear-gradient(90deg, #e75480, #ff9eb7);
                margin-top: 0.15rem;
                margin-bottom: 0.75rem;
            }

            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #fff8fb, #fff3f8);
            }

            [data-testid="stMetricValue"] {
                color: #5d5267;
            }
        </style>
        """,
        unsafe_allow_html=True,
)


def pink_line_chart(series: pd.Series, x_label: str, y_label: str) -> None:
    chart_df = series.reset_index()
    chart_df.columns = [x_label, y_label]
    line = (
        alt.Chart(chart_df)
        .mark_line(color=PINK, strokeWidth=3)
        .encode(
            x=alt.X(f"{x_label}:T"),
            y=alt.Y(f"{y_label}:Q"),
            tooltip=[x_label, y_label],
        )
    )

    points = (
        alt.Chart(chart_df)
        .mark_circle(color=PINK, size=70)
        .encode(
            x=alt.X(f"{x_label}:T"),
            y=alt.Y(f"{y_label}:Q"),
            tooltip=[x_label, y_label],
        )
    )

    chart = (line + points).properties(height=260).configure_range(category=[PINK])
    st.altair_chart(chart, use_container_width=True)


def pink_bar_chart(series: pd.Series, x_label: str, y_label: str) -> None:
    chart_df = series.reset_index()
    chart_df.columns = [x_label, y_label]
    chart = (
        alt.Chart(chart_df)
        .mark_bar(color=PINK, cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X(f"{x_label}:N", sort=None),
            y=alt.Y(f"{y_label}:Q"),
            tooltip=[x_label, y_label],
        )
        .properties(height=260)
    )
    st.altair_chart(chart, use_container_width=True)

st.markdown("<h1 class='monitor-title'>LifeStyled Monitoring Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<hr class='monitor-divider' />", unsafe_allow_html=True)
st.caption("Operational and feedback metrics from request logs")

if not EVENT_LOG_PATH.exists():
    st.warning("No events found yet. Use the main app page and submit feedback first.")
    st.stop()

rows = []
with EVENT_LOG_PATH.open("r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue

if not rows:
    st.warning("Event log exists but has no valid rows yet.")
    st.stop()

df = pd.DataFrame(rows)
df["dt"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")
df = df.dropna(subset=["dt"]).sort_values("dt")

if df.empty:
    st.warning("No valid timestamps in event logs.")
    st.stop()

df["date"] = df["dt"].dt.date
df["hour"] = df["dt"].dt.floor("h")
df["budget_mid"] = (pd.to_numeric(df["profile"].apply(lambda x: x.get("budget_min", 0))) + pd.to_numeric(df["profile"].apply(lambda x: x.get("budget_max", 0)))) / 2

st.subheader("Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total requests", int(len(df)))
col2.metric("Avg response time (ms)", round(float(df["response_time_ms"].mean()), 2))
col3.metric("Avg feedback", round(float(df["feedback"].mean()), 2))
col4.metric("Hybrid usage %", round(100 * float((df["retrieval_mode"] == "hybrid").mean()), 1))

st.subheader("1) Requests over time")
requests_over_time = df.groupby("hour").size().rename("requests")
pink_line_chart(requests_over_time, "hour", "requests")

st.subheader("2) Avg response time over time")
latency_over_time = df.groupby("hour")["response_time_ms"].mean()
pink_line_chart(latency_over_time, "hour", "response_time_ms")

st.subheader("3) Feedback trend")
feedback_over_time = df.groupby("hour")["feedback"].mean()
pink_line_chart(feedback_over_time, "hour", "feedback")

st.subheader("4) Top categories requested")
cat_lookup = {}
if CATALOG_PATH.exists():
    catalog_df = pd.read_csv(CATALOG_PATH)
    cat_lookup = dict(zip(catalog_df["product_id"], catalog_df["category"]))

cat_counter = {}
for ids in df["result_ids"].dropna():
    if not isinstance(ids, list):
        continue
    for pid in ids:
        category = cat_lookup.get(pid, "unknown")
        cat_counter[category] = cat_counter.get(category, 0) + 1

cat_df = pd.DataFrame(
    [{"category": k, "count": v} for k, v in sorted(cat_counter.items(), key=lambda x: x[1], reverse=True)]
)
if not cat_df.empty:
    pink_bar_chart(cat_df.set_index("category")["count"], "category", "count")
else:
    st.info("No category-like counts yet.")

st.subheader("5) Budget band distribution")
budget_bins = pd.cut(df["budget_mid"], bins=[0, 50, 100, 150, 250, 9999], labels=["0-50", "51-100", "101-150", "151-250", "250+"])
budget_dist = budget_bins.value_counts().sort_index()
pink_bar_chart(budget_dist, "budget_band", "count")

st.subheader("Optional diagnostics")
if "prompt_variant" in df.columns:
    prompt_usage = df["prompt_variant"].fillna("none").value_counts()
    st.write("Prompt variant usage")
    pink_bar_chart(prompt_usage, "prompt_variant", "count")

st.dataframe(df.tail(50), use_container_width=True)
