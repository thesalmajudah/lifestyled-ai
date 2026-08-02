import json
from pathlib import Path
from typing import Dict, List

import chromadb
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from .config import BM25_STATE_PATH, CHROMA_DIR, RAW_DATA_PATH, VECTORIZER_PATH


def _split_tags(value: str) -> List[str]:
    return [tag.strip() for tag in str(value).split("|") if tag.strip()]


def _build_document_text(row: pd.Series) -> str:
    parts = [
        f"Title: {row['title']}",
        f"Category: {row['category']}",
        f"Brand: {row['brand']}",
        f"Price: {row['price']}",
        f"Style tags: {row['style_tags']}",
        f"Lifestyle tags: {row['lifestyle_tags']}",
        f"Climate tags: {row['climate_tags']}",
        f"Occasion tags: {row['occasion_tags']}",
        f"Description: {row['description']}",
    ]
    return "\n".join(parts)


def _row_to_metadata(row: pd.Series) -> Dict[str, str]:
    return {
        "product_id": str(row["product_id"]),
        "title": str(row["title"]),
        "category": str(row["category"]),
        "brand": str(row["brand"]),
        "price": float(row["price"]),
        "colors": str(row["colors"]),
        "sizes": str(row["sizes"]),
        "style_tags": str(row["style_tags"]),
        "lifestyle_tags": str(row["lifestyle_tags"]),
        "climate_tags": str(row["climate_tags"]),
        "occasion_tags": str(row["occasion_tags"]),
        "description": str(row["description"]),
        "stock_status": str(row["stock_status"]),
    }


def build_index(
    data_path: Path = RAW_DATA_PATH,
    chroma_dir: Path = CHROMA_DIR,
    bm25_state_path: Path = BM25_STATE_PATH,
    collection_name: str = "products",
) -> None:
    df = pd.read_csv(data_path)
    if df.empty:
        raise ValueError("Input dataset is empty")

    documents = []
    metadatas = []
    ids = []
    tokenized_corpus = []

    for _, row in df.iterrows():
        doc_text = _build_document_text(row)
        metadata = _row_to_metadata(row)

        documents.append(doc_text)
        metadatas.append(metadata)
        ids.append(str(row["product_id"]))

        bm25_tokens = []
        for field in ["title", "category", "brand", "description"]:
            bm25_tokens.extend(str(row[field]).lower().split())
        for tag_field in ["style_tags", "lifestyle_tags", "climate_tags", "occasion_tags"]:
            bm25_tokens.extend(_split_tags(row[tag_field]))
        tokenized_corpus.append(bm25_tokens)

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_features=1024,
    )
    tfidf_matrix = vectorizer.fit_transform(documents)
    embeddings = tfidf_matrix.toarray().tolist()

    chroma_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir))
    # Recreate the collection to handle embedding dimension changes safely.
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
    collection = client.create_collection(name=collection_name)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    bm25_state_path.parent.mkdir(parents=True, exist_ok=True)
    with bm25_state_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "ids": ids,
                "tokenized_corpus": tokenized_corpus,
                "metadatas": metadatas,
                "documents": documents,
            },
            f,
            ensure_ascii=True,
            indent=2,
        )

    joblib.dump(vectorizer, VECTORIZER_PATH)


def load_catalog(data_path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    return pd.read_csv(data_path)
