from __future__ import annotations

import re
import time
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Dict, List

from .models import SearchResult, UserProfile
from .retrieval import ProductRetriever


@dataclass
class AgentStep:
    step: int
    action: str
    input_summary: str
    output_summary: str
    latency_ms: float


@dataclass
class AgentRunResult:
    results: List[SearchResult]
    final_query: str
    quality_score: float
    stop_reason: str
    steps: List[AgentStep]

    def steps_as_dicts(self) -> List[Dict[str, str]]:
        return [asdict(step) for step in self.steps]


class AgenticRecommender:
    def __init__(
        self,
        retriever: ProductRetriever,
        quality_threshold: float = 0.56,
        diversity_penalty: float = 0.02,
    ) -> None:
        self.retriever = retriever
        self.quality_threshold = quality_threshold
        self.diversity_penalty = diversity_penalty

    def _quality_proxy(self, results: List[SearchResult], k: int) -> float:
        if not results:
            return 0.0

        top = results[:k]
        avg_score = sum(item.score for item in top) / len(top)
        unique_categories = len({item.category for item in top}) / max(1, len(top))
        return round(0.85 * avg_score + 0.15 * unique_categories, 4)

    def _rewrite_query(self, query: str, profile: UserProfile) -> str:
        style = (profile.style_tags[0] if profile.style_tags else "minimal").strip().lower()
        lifestyle = (profile.lifestyle_tags[0] if profile.lifestyle_tags else "daily").strip().lower()
        climate = (profile.climate_tags[0] if profile.climate_tags else "mild").strip().lower()
        occasion = (profile.occasion_tags[0] if profile.occasion_tags else "casual").strip().lower()

        hint = "versatile pieces"
        if occasion in {"work", "formal"} or lifestyle in {"office", "commute"}:
            hint = "workwear tops, bottoms, or dresses"
        elif lifestyle in {"vacation", "travel"}:
            hint = "packable travel-ready pieces"
        elif occasion in {"active"} or lifestyle in {"gym", "hiking"}:
            hint = "performance activewear"

        rewritten = (
            f"{query}. Prioritize {style} {hint} for {lifestyle} in {climate} weather for {occasion}."
        )
        rewritten = re.sub(r"\s+", " ", rewritten).strip()
        return rewritten

    def _rerank_with_diversity(self, results: List[SearchResult], k: int) -> List[SearchResult]:
        if not results:
            return []

        category_counts: Counter[str] = Counter()
        adjusted: List[SearchResult] = []
        for item in results[: max(k * 3, k)]:
            penalty = self.diversity_penalty * category_counts[item.category]
            adjusted_score = max(0.0, item.score - penalty)
            adjusted.append(
                SearchResult(
                    product_id=item.product_id,
                    title=item.title,
                    brand=item.brand,
                    category=item.category,
                    price=item.price,
                    score=round(adjusted_score, 4),
                    reason=item.reason,
                )
            )
            category_counts[item.category] += 1

        adjusted.sort(key=lambda row: row.score, reverse=True)
        return adjusted[:k]

    def run(
        self,
        query: str,
        profile: UserProfile,
        retrieval_mode: str = "hybrid",
        k: int = 5,
    ) -> AgentRunResult:
        steps: List[AgentStep] = []

        t0 = time.perf_counter()
        initial = self.retriever.search(query=query, profile=profile, retrieval_mode=retrieval_mode, k=max(k * 3, 10))
        q_initial = self._quality_proxy(initial, k)
        steps.append(
            AgentStep(
                step=1,
                action="retrieve",
                input_summary=f"mode={retrieval_mode}; query={query}",
                output_summary=f"candidates={len(initial)}; quality={q_initial}",
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            )
        )

        best_results = initial
        best_query = query
        best_quality = q_initial
        stop_reason = "quality_sufficient"

        if retrieval_mode == "hybrid" and q_initial < self.quality_threshold:
            rewritten_query = self._rewrite_query(query, profile)

            t1 = time.perf_counter()
            rewritten_results = self.retriever.search(
                query=rewritten_query,
                profile=profile,
                retrieval_mode=retrieval_mode,
                k=max(k * 3, 10),
            )
            q_rewrite = self._quality_proxy(rewritten_results, k)
            steps.append(
                AgentStep(
                    step=2,
                    action="rewrite_and_retrieve",
                    input_summary=f"rewritten_query={rewritten_query}",
                    output_summary=f"candidates={len(rewritten_results)}; quality={q_rewrite}",
                    latency_ms=round((time.perf_counter() - t1) * 1000, 2),
                )
            )

            if q_rewrite >= q_initial:
                best_results = rewritten_results
                best_query = rewritten_query
                best_quality = q_rewrite
                stop_reason = "rewrite_improved_or_equal"
            else:
                stop_reason = "rewrite_not_better"

        t2 = time.perf_counter()
        reranked = self._rerank_with_diversity(best_results, k=k)
        steps.append(
            AgentStep(
                step=3,
                action="rerank_diversity",
                input_summary=f"input_candidates={len(best_results)}",
                output_summary=f"returned={len(reranked)}",
                latency_ms=round((time.perf_counter() - t2) * 1000, 2),
            )
        )

        return AgentRunResult(
            results=reranked,
            final_query=best_query,
            quality_score=best_quality,
            stop_reason=stop_reason,
            steps=steps,
        )
