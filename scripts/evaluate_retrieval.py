import json
from pathlib import Path
import sys
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lifestyled.models import UserProfile
from lifestyled.retrieval import ProductRetriever


EVAL_PATH = ROOT_DIR / "data" / "eval" / "validation_queries.json"
REPORT_JSON_PATH = ROOT_DIR / "reports" / "retrieval_eval.json"
REPORT_MD_PATH = ROOT_DIR / "reports" / "retrieval_eval.md"


def hit_rate_at_k(predicted_ids: List[str], expected_ids: List[str], k: int) -> float:
    return 1.0 if set(predicted_ids[:k]).intersection(set(expected_ids)) else 0.0


def relevance_at_k(predicted_ids: List[str], expected_ids: List[str], k: int) -> float:
    overlap = len(set(predicted_ids[:k]).intersection(set(expected_ids)))
    denom = max(1, min(k, len(expected_ids)))
    return overlap / denom


def evaluate_mode(retriever: ProductRetriever, cases: List[Dict], mode: str, k: int = 5) -> Dict:
    rows = []
    for case in cases:
        profile = UserProfile(**case["profile"])
        results = retriever.search(case["query"], profile=profile, retrieval_mode=mode, k=k)
        predicted_ids = [r.product_id for r in results]
        expected_ids = case["expected_ids"]

        rows.append(
            {
                "id": case["id"],
                "query": case["query"],
                "predicted_ids": predicted_ids,
                "expected_ids": expected_ids,
                "hit_rate_at_k": round(hit_rate_at_k(predicted_ids, expected_ids, k), 4),
                "relevance_at_k": round(relevance_at_k(predicted_ids, expected_ids, k), 4),
            }
        )

    avg_hit = sum(r["hit_rate_at_k"] for r in rows) / max(1, len(rows))
    avg_rel = sum(r["relevance_at_k"] for r in rows) / max(1, len(rows))

    return {
        "mode": mode,
        "k": k,
        "avg_hit_rate_at_k": round(avg_hit, 4),
        "avg_relevance_at_k": round(avg_rel, 4),
        "cases": rows,
    }


def write_markdown_report(report: Dict) -> None:
    vector = report["vector"]
    hybrid = report["hybrid"]

    lines = [
        "# Retrieval Evaluation",
        "",
        f"k = {vector['k']}",
        "",
        "## Summary",
        "",
        "| Mode | Avg Hit Rate@k | Avg Relevance@k |",
        "|---|---:|---:|",
        f"| vector | {vector['avg_hit_rate_at_k']} | {vector['avg_relevance_at_k']} |",
        f"| hybrid | {hybrid['avg_hit_rate_at_k']} | {hybrid['avg_relevance_at_k']} |",
        "",
        "## Per-query Results",
        "",
        "| Query ID | Mode | Hit@k | Relevance@k | Predicted IDs | Expected IDs |",
        "|---|---|---:|---:|---|---|",
    ]

    for mode in ["vector", "hybrid"]:
        for row in report[mode]["cases"]:
            lines.append(
                f"| {row['id']} | {mode} | {row['hit_rate_at_k']} | {row['relevance_at_k']} | {' ,'.join(row['predicted_ids'])} | {' ,'.join(row['expected_ids'])} |"
            )

    REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not EVAL_PATH.exists():
        raise FileNotFoundError(f"Validation set not found: {EVAL_PATH}")

    with EVAL_PATH.open("r", encoding="utf-8") as f:
        cases = json.load(f)

    retriever = ProductRetriever()
    vector_report = evaluate_mode(retriever, cases, mode="vector", k=5)
    hybrid_report = evaluate_mode(retriever, cases, mode="hybrid", k=5)

    report = {"vector": vector_report, "hybrid": hybrid_report}

    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=True, indent=2)

    write_markdown_report(report)
    print(f"Saved: {REPORT_JSON_PATH}")
    print(f"Saved: {REPORT_MD_PATH}")


if __name__ == "__main__":
    main()
