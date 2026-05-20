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
    candidates = [RESOURCE_DIR.joinpath(*parts)]
    if getattr(sys, "frozen", False) and sys.platform == "darwin":
        executable_path = Path(sys.executable).resolve()
        contents_dir = executable_path.parent.parent
        candidates.extend(
            [
                contents_dir / "Resources" / Path(*parts),
                executable_path.parent / Path(*parts),
            ]
        )
    candidates.append(ROOT_DIR.joinpath(*parts))

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


DATA_DIR = app_data_dir()
POSTERS_DIR = DATA_DIR / "posters"
CACHE_DIR = DATA_DIR / "cache"
DATABASE_PATH = DATA_DIR / "media.db"


def ensure_data_dirs() -> None:
    POSTERS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
