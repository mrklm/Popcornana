from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
POSTERS_DIR = DATA_DIR / "posters"
CACHE_DIR = DATA_DIR / "cache"
DATABASE_PATH = ROOT_DIR / "media.db"


def ensure_data_dirs() -> None:
    POSTERS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
