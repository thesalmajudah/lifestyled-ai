from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "products_seed.csv"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DIR = PROCESSED_DIR / "chroma"
BM25_STATE_PATH = PROCESSED_DIR / "bm25_state.json"
EVENT_LOG_PATH = ROOT_DIR / "logs" / "events.jsonl"
