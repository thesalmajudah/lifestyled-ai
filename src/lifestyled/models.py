from dataclasses import dataclass
from typing import List


@dataclass
class UserProfile:
    style_tags: List[str]
    lifestyle_tags: List[str]
    climate_tags: List[str]
    occasion_tags: List[str]
    budget_min: float
    budget_max: float
    size: str


@dataclass
class SearchResult:
    product_id: str
    title: str
    brand: str
    category: str
    price: float
    score: float
    reason: str
