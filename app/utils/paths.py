from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", ROOT_DIR))


def app_data_dir() -> Path:
    if not getattr(sys, "frozen", False):
        return ROOT_DIR / "data"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Popcornana"
    if os.name == "nt":
        return Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "Popcornana"
    return Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "Popcornana"


def resource_path(*parts: str) -> Path:
    return RESOURCE_DIR.joinpath(*parts)


DATA_DIR = app_data_dir()
POSTERS_DIR = DATA_DIR / "posters"
CACHE_DIR = DATA_DIR / "cache"
DATABASE_PATH = DATA_DIR / "media.db"


def ensure_data_dirs() -> None:
    POSTERS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
