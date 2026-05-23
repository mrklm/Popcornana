from __future__ import annotations

import sys
from pathlib import Path


FALLBACK_VERSION = "1.0.50"


def read_app_version() -> str:
    root_dir = Path(__file__).resolve().parents[1]
    resource_dir = Path(getattr(sys, "_MEIPASS", root_dir.parent))
    candidates = [
        resource_dir / "VERSION",
        root_dir.parent / "VERSION",
    ]
    for candidate in candidates:
        if candidate.exists():
            version = candidate.read_text(encoding="utf-8").strip()
            if version:
                return version
    return FALLBACK_VERSION


APP_VERSION = read_app_version()
