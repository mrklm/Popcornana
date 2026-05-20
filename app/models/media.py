from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class MediaItem:
    filepath: Path
    media_type: str
    title: str
    year: int | None = None
    original_title: str | None = None
    overview: str | None = None
    genres: str | None = None
    vote_average: float | None = None
    poster_path: str | None = None
    backdrop_path: str | None = None
    tmdb_id: int | None = None
    season: int | None = None
    episode: int | None = None

    @property
    def display_year(self) -> str:
        return str(self.year) if self.year else ""
