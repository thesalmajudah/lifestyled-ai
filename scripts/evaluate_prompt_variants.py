import json
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

load_dotenv(ROOT_DIR / ".env")

from lifestyled.explanations import generate_explanation
from lifestyled.models import UserProfile
from lifestyled.retrieval import ProductRetriever

EVAL_PATH = ROOT_DIR / "data" / "eval" / "validation_queries.json"
OUTPUT_PATH = ROOT_DIR / "reports" / "prompt_variant_outputs.json"


def main() -> None:
    if not os.getenv("GROQ_API_KEY", "").strip():
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to .env and rerun this script."
        )

    with EVAL_PATH.open("r", encoding="utf-8") as f:
        cases = json.load(f)

    retriever = ProductRetriever()
    outputs = []

    for case in cases:
        profile = UserProfile(**case["profile"])
        results = retriever.search(case["query"], profile=profile, retrieval_mode="hybrid", k=1)
        if not results:
            continue

        top_item = results[0]
        a_text = generate_explanation(case["query"], profile, top_item, prompt_variant="A")
        b_text = generate_explanation(case["query"], profile, top_item, prompt_variant="B")

        outputs.append(
            {
                "id": case["id"],
                "query": case["query"],
                "top_item_id": top_item.product_id,
                "prompt_a": a_text,
                "prompt_b": b_text,
                "manual_scores": {
                    "relevance": {"A": None, "B": None},
                    "groundedness": {"A": None, "B": None},
                    "personalization": {"A": None, "B": None},
                    "clarity": {"A": None, "B": None}
                }
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(outputs, f, ensure_ascii=True, indent=2)

    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
