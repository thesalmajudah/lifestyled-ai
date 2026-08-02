import json
from pathlib import Path
from statistics import mean

ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT_DIR / "reports" / "prompt_variant_outputs.json"
OUTPUT_PATH = ROOT_DIR / "reports" / "prompt_variant_scoring.md"

DIMENSIONS = ["relevance", "groundedness", "personalization", "clarity"]


def _valid_score(value):
    return isinstance(value, (int, float)) and 1 <= value <= 5


def _avg(values):
    return round(mean(values), 3) if values else None


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Missing {INPUT_PATH}. Run evaluate_prompt_variants.py first."
        )

    with INPUT_PATH.open("r", encoding="utf-8") as f:
        rows = json.load(f)

    scores = {
        "A": {d: [] for d in DIMENSIONS},
        "B": {d: [] for d in DIMENSIONS},
    }

    total_slots = 0
    filled_slots = 0

    for row in rows:
        manual = row.get("manual_scores", {})
        for d in DIMENSIONS:
            variants = manual.get(d, {})
            for v in ["A", "B"]:
                total_slots += 1
                val = variants.get(v)
                if _valid_score(val):
                    filled_slots += 1
                    scores[v][d].append(float(val))

    coverage = 0.0 if total_slots == 0 else round((filled_slots / total_slots) * 100, 2)

    a_dim = {d: _avg(scores["A"][d]) for d in DIMENSIONS}
    b_dim = {d: _avg(scores["B"][d]) for d in DIMENSIONS}

    a_overall_values = [v for v in a_dim.values() if v is not None]
    b_overall_values = [v for v in b_dim.values() if v is not None]

    a_overall = _avg(a_overall_values)
    b_overall = _avg(b_overall_values)

    recommendation = "insufficient_data"
    if a_overall is not None and b_overall is not None:
        if a_overall > b_overall:
            recommendation = "A"
        elif b_overall > a_overall:
            recommendation = "B"
        else:
            recommendation = "tie"

    lines = [
        "# Prompt Variant Scoring",
        "",
        f"Input file: {INPUT_PATH}",
        f"Scoring coverage: {filled_slots}/{total_slots} ({coverage}%)",
        "",
        "Score rubric: 1 (poor) to 5 (excellent)",
        "",
        "## Dimension Averages",
        "",
        "| Dimension | Prompt A | Prompt B |",
        "|---|---:|---:|",
    ]

    for d in DIMENSIONS:
        a_val = "-" if a_dim[d] is None else str(a_dim[d])
        b_val = "-" if b_dim[d] is None else str(b_dim[d])
        lines.append(f"| {d} | {a_val} | {b_val} |")

    lines.extend(
        [
            "",
            "## Overall",
            "",
            f"- Prompt A: {'-' if a_overall is None else a_overall}",
            f"- Prompt B: {'-' if b_overall is None else b_overall}",
            f"- Recommendation: {recommendation}",
            "",
            "## Notes",
            "",
            "- If recommendation is insufficient_data, fill manual_scores in prompt_variant_outputs.json and rerun this script.",
            "- Keep a short rationale in README when choosing default prompt.",
        ]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
