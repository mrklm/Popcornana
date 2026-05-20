from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv
from os import getenv
from rapidfuzz import fuzz

from app.models.media import MediaItem
from app.utils.paths import POSTERS_DIR


TMDB_API_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER_KEYS = {"", "xxxxxxxx", "xxxx", "ta_cle_tmdb", "ta_cle_tmdb_ici"}


@dataclass
class TmdbResult:
    tmdb_id: int
    media_type: str
    title: str
    original_title: str | None
    year: int | None
    overview: str | None
    poster_path: str | None
    backdrop_path: str | None
    vote_average: float | None
    score: float


class TmdbClient:
    def __init__(self, api_key: str | None = None) -> None:
        load_dotenv()
        self.api_key = api_key or getenv("TMDB_API_KEY")
        self.session = requests.Session()

    def set_api_key(self, api_key: str | None) -> None:
        self.api_key = api_key

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip().lower() not in PLACEHOLDER_KEYS)

    def search(self, item: MediaItem) -> list[TmdbResult]:
        if not self.api_key:
            return []

        endpoint = "search/tv" if item.media_type == "tv" else "search/movie"
        params = {
                "api_key": self.api_key,
                "query": item.title,
                "language": "fr-FR",
                "include_adult": "false",
                "year": item.year if item.media_type == "movie" else None,
                "first_air_date_year": item.year if item.media_type == "tv" else None,
        }
        response = self.session.get(
            f"{TMDB_API_BASE}/{endpoint}",
            params={key: value for key, value in params.items() if value is not None},
            timeout=15,
        )
        response.raise_for_status()
        return [self._result_from_payload(payload, item) for payload in response.json().get("results", [])]

    def enrich_automatically(self, item: MediaItem) -> MediaItem:
        results = self.search(item)
        if not results:
            return item

        best = max(results, key=lambda result: result.score)
        year_ok = not item.year or not best.year or abs(item.year - best.year) <= 1
        if best.score >= 86 and year_ok:
            return apply_tmdb_result(item, best)
        if len(results) == 1 and best.score >= 75 and year_ok:
            return apply_tmdb_result(item, best)
        return item

    def download_poster(self, poster_path: str | None) -> Path | None:
        if not poster_path:
            return None

        POSTERS_DIR.mkdir(parents=True, exist_ok=True)
        target = POSTERS_DIR / poster_path.lstrip("/")
        if target.exists():
            return target

        response = self.session.get(f"{TMDB_IMAGE_BASE}{poster_path}", timeout=20)
        response.raise_for_status()
        target.write_bytes(response.content)
        return target

    @staticmethod
    def _result_from_payload(payload: dict, item: MediaItem) -> TmdbResult:
        title = payload.get("title") or payload.get("name") or ""
        original_title = payload.get("original_title") or payload.get("original_name")
        release_date = payload.get("release_date") or payload.get("first_air_date") or ""
        year = int(release_date[:4]) if release_date[:4].isdigit() else None
        score = float(fuzz.token_set_ratio(item.title, title))
        if item.year and year and item.year == year:
            score += 8
        return TmdbResult(
            tmdb_id=int(payload["id"]),
            media_type=item.media_type,
            title=title,
            original_title=original_title,
            year=year,
            overview=payload.get("overview"),
            poster_path=payload.get("poster_path"),
            backdrop_path=payload.get("backdrop_path"),
            vote_average=payload.get("vote_average"),
            score=min(score, 100),
        )


def apply_tmdb_result(item: MediaItem, result: TmdbResult) -> MediaItem:
    item.tmdb_id = result.tmdb_id
    item.title = result.title or item.title
    item.original_title = result.original_title
    item.year = result.year or item.year
    item.overview = result.overview
    item.poster_path = result.poster_path
    item.backdrop_path = result.backdrop_path
    item.vote_average = result.vote_average
    return item
