from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from os import getenv
from rapidfuzz import fuzz

from app.models.media import MediaItem
from app.utils.paths import POSTERS_DIR


OMDB_API_BASE = "https://www.omdbapi.com/"
PLACEHOLDER_KEYS = {"", "xxxxxxxx", "xxxx", "ta_cle_omdb", "ta_cle_omdb_ici"}


@dataclass
class OmdbResult:
    imdb_id: str
    media_type: str
    title: str
    year: int | None
    overview: str | None
    genres: str | None
    director: str | None
    runtime_minutes: int | None
    poster_url: str | None
    vote_average: float | None
    score: float


class OmdbClient:
    def __init__(self, api_key: str | None = None) -> None:
        load_dotenv()
        self.api_key = api_key or getenv("OMDB_API_KEY")
        self.session = requests.Session()

    def set_api_key(self, api_key: str | None) -> None:
        self.api_key = api_key

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip().lower() not in PLACEHOLDER_KEYS)

    def search(self, item: MediaItem) -> list[OmdbResult]:
        if not self.is_configured:
            return []

        params = {
            "apikey": self.api_key,
            "s": item.title,
            "type": "series" if item.media_type == "tv" else "movie",
            "y": item.year,
        }
        response = self.session.get(OMDB_API_BASE, params=_without_empty_values(params), timeout=15)
        response.raise_for_status()
        payload = response.json()
        if payload.get("Response") != "True":
            return []

        results = []
        for match in payload.get("Search", []):
            imdb_id = match.get("imdbID")
            if not imdb_id:
                continue
            details = self.details(imdb_id)
            if details:
                results.append(score_omdb_result(details, item))
        return results

    def details(self, imdb_id: str) -> OmdbResult | None:
        if not self.is_configured:
            return None

        response = self.session.get(
            OMDB_API_BASE,
            params={"apikey": self.api_key, "i": imdb_id, "plot": "full"},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("Response") != "True":
            return None
        return self._result_from_payload(payload)

    def enrich_automatically(self, item: MediaItem) -> MediaItem:
        results = self.search(item)
        if not results:
            return item

        best = max(results, key=lambda result: result.score)
        year_ok = not item.year or not best.year or abs(item.year - best.year) <= 1
        if best.score >= 86 and year_ok:
            return self._apply_and_cache_poster(item, best)
        if len(results) == 1 and best.score >= 75 and year_ok:
            return self._apply_and_cache_poster(item, best)
        return item

    def download_poster(self, result: OmdbResult | MediaItem | None) -> Path | None:
        if result is None:
            return None

        poster_url = result.poster_url if isinstance(result, OmdbResult) else result.poster_path
        imdb_id = result.imdb_id if isinstance(result, OmdbResult) else None
        if not poster_url or poster_url == "N/A" or not poster_url.startswith(("http://", "https://")):
            return None

        extension = Path(urlparse(poster_url).path).suffix or ".jpg"
        filename = f"{imdb_id or abs(hash(poster_url))}{extension}"
        target = POSTERS_DIR / "omdb" / filename
        if target.exists():
            return target

        target.parent.mkdir(parents=True, exist_ok=True)
        response = self.session.get(poster_url, timeout=20)
        response.raise_for_status()
        target.write_bytes(response.content)
        return target

    @staticmethod
    def _result_from_payload(payload: dict) -> OmdbResult:
        title = payload.get("Title") or ""
        year = _parse_year(payload.get("Year"))
        imdb_rating = _parse_rating(payload.get("imdbRating"))
        poster_url = payload.get("Poster")
        if poster_url == "N/A":
            poster_url = None

        return OmdbResult(
            imdb_id=payload.get("imdbID") or "",
            media_type="tv" if payload.get("Type") == "series" else "movie",
            title=title,
            year=year,
            overview=_none_if_na(payload.get("Plot")),
            genres=_none_if_na(payload.get("Genre")),
            director=_none_if_na(payload.get("Director")),
            runtime_minutes=_parse_runtime(payload.get("Runtime")),
            poster_url=poster_url,
            vote_average=imdb_rating,
            score=0,
        )

    def _apply_and_cache_poster(self, item: MediaItem, result: OmdbResult) -> MediaItem:
        item = apply_omdb_result(item, result)
        poster = self.download_poster(result)
        if poster:
            item.poster_path = str(poster.relative_to(POSTERS_DIR))
        return item


def apply_omdb_result(item: MediaItem, result: OmdbResult) -> MediaItem:
    item.title = result.title or item.title
    item.year = result.year or item.year
    item.overview = result.overview or item.overview
    item.genres = result.genres or item.genres
    item.director = result.director or item.director
    item.runtime_minutes = result.runtime_minutes or item.runtime_minutes
    item.vote_average = result.vote_average or item.vote_average
    if result.poster_url:
        item.poster_path = result.poster_url
    return item


def score_omdb_result(result: OmdbResult, item: MediaItem) -> OmdbResult:
    score = float(fuzz.token_set_ratio(item.title, result.title))
    if item.year and result.year and item.year == result.year:
        score += 8
    result.score = min(score, 100)
    return result


def _without_empty_values(params: dict) -> dict:
    return {key: value for key, value in params.items() if value is not None}


def _parse_year(value: str | None) -> int | None:
    if not value:
        return None
    year = value[:4]
    return int(year) if year.isdigit() else None


def _parse_rating(value: str | None) -> float | None:
    if not value or value == "N/A":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_runtime(value: str | None) -> int | None:
    if not value or value == "N/A":
        return None
    number = value.split()[0]
    return int(number) if number.isdigit() else None


def _none_if_na(value: str | None) -> str | None:
    if not value or value == "N/A":
        return None
    return value
