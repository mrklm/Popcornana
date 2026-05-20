from __future__ import annotations

import re
from pathlib import Path


VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov"}

NOISE_TOKENS = {
    "1080p",
    "2160p",
    "720p",
    "480p",
    "x264",
    "x265",
    "h264",
    "h265",
    "bluray",
    "brrip",
    "web",
    "dl",
    "webrip",
    "web-dl",
    "webdl",
    "hdrip",
    "dvdrip",
    "multi",
    "french",
    "truefrench",
    "vostfr",
    "aac",
    "ac3",
    "dts",
    "hdr",
    "remux",
    "proper",
    "repack",
    "extended",
}

EPISODE_PATTERNS = (
    re.compile(r"\bS(?P<season>\d{1,2})E(?P<episode>\d{1,3})\b", re.IGNORECASE),
    re.compile(r"\b(?P<season>\d{1,2})x(?P<episode>\d{1,3})\b", re.IGNORECASE),
    re.compile(r"\bSeason[ ._-]?(?P<season>\d{1,2})[ ._-]+Episode[ ._-]?(?P<episode>\d{1,3})\b", re.IGNORECASE),
    re.compile(r"\bSaison[ ._-]?(?P<season>\d{1,2})[ ._-]+(?:Episode|Épisode)[ ._-]?(?P<episode>\d{1,3})\b", re.IGNORECASE),
)

YEAR_PATTERN = re.compile(r"(?:^|[ ._(-])(?P<year>19\d{2}|20\d{2})(?:$|[ ._)-])")
SEASON_FOLDER_PATTERN = re.compile(r"\b(?:Season|Saison|S)[ ._-]?(?P<season>\d{1,2})\b", re.IGNORECASE)
EPISODE_ONLY_PATTERN = re.compile(r"\b(?:Episode|Épisode|Ep|E)[ ._-]?(?P<episode>\d{1,3})\b", re.IGNORECASE)


def is_video_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS


def parse_media_filename(path: Path) -> dict[str, int | str | None]:
    stem = path.stem
    media_type = "movie"
    season = None
    episode = None

    for pattern in EPISODE_PATTERNS:
        match = pattern.search(stem)
        if match:
            media_type = "tv"
            season = int(match.group("season"))
            episode = int(match.group("episode"))
            stem = stem[: match.start()]
            break

    if media_type == "movie":
        season_from_folder = find_season_from_parent(path)
        episode_match = EPISODE_ONLY_PATTERN.search(stem)
        if season_from_folder and episode_match:
            media_type = "tv"
            season = season_from_folder
            episode = int(episode_match.group("episode"))
            stem = stem[: episode_match.start()]

    year = None
    year_match = YEAR_PATTERN.search(stem)
    if year_match:
        year = int(year_match.group("year"))
        stem = stem[: year_match.start()] + " " + stem[year_match.end() :]

    title = clean_title(stem)
    if not title:
        title = parent_series_title(path) if media_type == "tv" else path.stem

    return {
        "media_type": media_type,
        "title": title,
        "year": year,
        "season": season,
        "episode": episode,
    }


def find_season_from_parent(path: Path) -> int | None:
    for parent in (path.parent, path.parent.parent):
        match = SEASON_FOLDER_PATTERN.search(parent.name)
        if match:
            return int(match.group("season"))
    return None


def parent_series_title(path: Path) -> str:
    parent = path.parent
    if SEASON_FOLDER_PATTERN.search(parent.name):
        parent = parent.parent
    return clean_title(parent.name)


def clean_title(raw_name: str) -> str:
    normalized = re.sub(r"[._\[\]{}()+-]+", " ", raw_name)
    tokens = []
    for token in normalized.split():
        if token.lower() in NOISE_TOKENS:
            continue
        if re.fullmatch(r"\d{3,4}p", token.lower()):
            continue
        tokens.append(token)
    return " ".join(tokens).strip()
