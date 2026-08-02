import json
import os
from dataclasses import asdict
from typing import Literal

from groq import Groq

from .models import SearchResult, UserProfile

PromptVariant = Literal["A", "B"]


def _prompt_a(query: str, profile: UserProfile, item: SearchResult) -> str:
    return (
        "You are a fashion assistant.\n"
        "Use only the provided product data and profile.\n"
        "Write 2-3 short bullets explaining fit with style, lifestyle, climate, occasion, and budget.\n"
        "If uncertain, say what is unknown.\n\n"
        f"User query: {query}\n"
        f"Profile: {json.dumps(asdict(profile), ensure_ascii=True)}\n"
        f"Product: {json.dumps(asdict(item), ensure_ascii=True)}\n"
    )


def _prompt_b(query: str, profile: UserProfile, item: SearchResult) -> str:
    return (
        "You are LifeStyled, an explainable recommendation assistant.\n"
        "Return strict JSON with keys: summary, reasons, cautions.\n"
        "- summary: one sentence\n"
        "- reasons: array of 3 concise reasons grounded in metadata\n"
        "- cautions: array of potential mismatch notes\n"
        "Do not invent facts outside the provided data.\n\n"
        f"User query: {query}\n"
        f"Profile: {json.dumps(asdict(profile), ensure_ascii=True)}\n"
        f"Product: {json.dumps(asdict(item), ensure_ascii=True)}\n"
    )


def generate_explanation(
    query: str,
    profile: UserProfile,
    item: SearchResult,
    prompt_variant: PromptVariant = "A",
    model: str | None = None,
) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    resolved_model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    if prompt_variant == "A":
        prompt = _prompt_a(query, profile, item)
    elif prompt_variant == "B":
        prompt = _prompt_b(query, profile, item)
    else:
        raise ValueError("prompt_variant must be 'A' or 'B'")

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=resolved_model,
        messages=[
            {"role": "system", "content": "Be concise, grounded, and factual."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    text = completion.choices[0].message.content or ""
    return text.strip()
