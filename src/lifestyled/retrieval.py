import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Tuple

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from .config import BM25_STATE_PATH, CHROMA_DIR
from .models import SearchResult, UserProfile


class ProductRetriever:
    def __init__(
        self,
        chroma_dir: Path = CHROMA_DIR,
        bm25_state_path: Path = BM25_STATE_PATH,
        collection_name: str = "products",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.embedding_model = SentenceTransformer(embedding_model)
        self.client = chromadb.PersistentClient(path=str(chroma_dir))
        self.collection = self.client.get_or_create_collection(name=collection_name)

        if not bm25_state_path.exists():
            raise FileNotFoundError(
                f"BM25 state file not found at {bm25_state_path}. Run ingestion first."
            )

        with bm25_state_path.open("r", encoding="utf-8") as f:
            state = json.load(f)

        self.ids = state["ids"]
        self.documents = state["documents"]
        self.metadatas = state["metadatas"]
        self.tokenized_corpus = state["tokenized_corpus"]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

        self.metadata_by_id = {
            item["product_id"]: item
            for item in self.metadatas
        }

    def _split_tags(self, value: str) -> List[str]:
        return [tag.strip().lower() for tag in str(value).split("|") if tag.strip()]

    def _profile_match_score(self, metadata: Dict[str, str], profile: UserProfile) -> Tuple[float, List[str]]:
        score = 0.0
        reasons = []

        style = set(self._split_tags(metadata["style_tags"]))
        lifestyle = set(self._split_tags(metadata["lifestyle_tags"]))
        climate = set(self._split_tags(metadata["climate_tags"]))
        occasion = set(self._split_tags(metadata["occasion_tags"]))

        style_hits = style.intersection(set([x.lower() for x in profile.style_tags]))
        lifestyle_hits = lifestyle.intersection(set([x.lower() for x in profile.lifestyle_tags]))
        climate_hits = climate.intersection(set([x.lower() for x in profile.climate_tags]))
        occasion_hits = occasion.intersection(set([x.lower() for x in profile.occasion_tags]))

        score += 0.30 * (len(style_hits) / max(1, len(profile.style_tags)))
        score += 0.25 * (len(lifestyle_hits) / max(1, len(profile.lifestyle_tags)))
        score += 0.20 * (len(climate_hits) / max(1, len(profile.climate_tags)))
        score += 0.15 * (len(occasion_hits) / max(1, len(profile.occasion_tags)))

        price = float(metadata["price"])
        if profile.budget_min <= price <= profile.budget_max:
            score += 0.10
            reasons.append("within budget")

        if style_hits:
            reasons.append(f"style match: {', '.join(sorted(style_hits))}")
        if lifestyle_hits:
            reasons.append(f"lifestyle match: {', '.join(sorted(lifestyle_hits))}")
        if climate_hits:
            reasons.append(f"climate match: {', '.join(sorted(climate_hits))}")
        if occasion_hits:
            reasons.append(f"occasion match: {', '.join(sorted(occasion_hits))}")

        return score, reasons

    def _passes_filters(self, metadata: Dict[str, str], profile: UserProfile) -> bool:
        sizes = [s.strip().lower() for s in str(metadata["sizes"]).split("|")]
        stock_ok = metadata.get("stock_status", "in_stock") in {"in_stock", "low_stock"}
        size_ok = profile.size.strip().lower() in sizes
        budget_ok = profile.budget_min <= float(metadata["price"]) <= profile.budget_max
        return stock_ok and size_ok and budget_ok

    def search(
        self,
        query: str,
        profile: UserProfile,
        k: int = 5,
        retrieval_mode: str = "hybrid",
    ) -> List[SearchResult]:
        if retrieval_mode not in {"vector", "hybrid"}:
            raise ValueError("retrieval_mode must be 'vector' or 'hybrid'")

        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True).tolist()[0]
        vector_hits = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(20, len(self.ids)),
            include=["metadatas", "distances"],
        )

        vector_scores = {}
        for meta, distance in zip(vector_hits["metadatas"][0], vector_hits["distances"][0]):
            # Convert distance to similarity-like score in [0, 1].
            sim = 1.0 / (1.0 + max(0.0, float(distance)))
            vector_scores[meta["product_id"]] = sim

        bm25_scores = {}
        if retrieval_mode == "hybrid":
            q_tokens = query.lower().split()
            raw_scores = self.bm25.get_scores(q_tokens)
            max_score = max(raw_scores) if len(raw_scores) > 0 else 1.0
            for idx, score in enumerate(raw_scores):
                bm25_scores[self.ids[idx]] = float(score / max(1e-9, max_score))

        ranked = []
        for product_id in self.ids:
            metadata = self.metadata_by_id[product_id]
            if not self._passes_filters(metadata, profile):
                continue

            profile_score, reasons = self._profile_match_score(metadata, profile)
            v_score = vector_scores.get(product_id, 0.0)
            b_score = bm25_scores.get(product_id, 0.0)

            if retrieval_mode == "vector":
                total_score = 0.7 * v_score + 0.3 * profile_score
            else:
                total_score = 0.5 * v_score + 0.2 * b_score + 0.3 * profile_score

            ranked.append(
                SearchResult(
                    product_id=product_id,
                    title=metadata["title"],
                    brand=metadata["brand"],
                    category=metadata["category"],
                    price=float(metadata["price"]),
                    score=round(total_score, 4),
                    reason="; ".join(reasons) if reasons else "matched by semantic relevance",
                )
            )

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:k]

    @staticmethod
    def profile_from_dict(payload: Dict[str, str]) -> UserProfile:
        return UserProfile(**payload)

    @staticmethod
    def result_to_dict(result: SearchResult) -> Dict[str, str]:
        return asdict(result)
