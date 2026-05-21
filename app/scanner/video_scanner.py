from __future__ import annotations

from pathlib import Path

from app.models.media import MediaItem
from app.scanner.name_cleaner import clean_title, is_video_file, parent_series_title, parse_media_filename


def scan_videos(folder: str | Path, category_overrides: dict[str, str] | None = None) -> list[MediaItem]:
    root = Path(folder).expanduser()
    if not root.exists():
        return []

    category_overrides = category_overrides or {}
    items: list[MediaItem] = []
    for path in sorted(root.rglob("*")):
        if not is_video_file(path):
            continue
        category, category_folder = category_for_path(root, path, category_overrides)
        if category == "ignore":
            continue
        parsed = parse_media_filename(path)
        title = str(parsed["title"])
        season = parsed["season"] if isinstance(parsed["season"], int) else None
        episode = parsed["episode"] if isinstance(parsed["episode"], int) else None
        media_type = str(parsed["media_type"])
        if category == "movie":
            media_type = "movie"
            title = clean_title(category_folder.name) if category_folder else title
            season = None
            episode = None
        elif category == "movie_folder":
            media_type = "movie"
            season = None
            episode = None
        elif category in {"tv", "series_folder"}:
            media_type = "tv"
            title = forced_series_title(path, category_folder) if category_folder else title
        items.append(
            MediaItem(
                filepath=path,
                media_type=media_type,
                title=title,
                year=parsed["year"] if isinstance(parsed["year"], int) else None,
                season=season,
                episode=episode,
                category_forced=category != "auto",
                category_override=category if category != "auto" else None,
            )
        )
    return items


def category_for_path(root: Path, path: Path, category_overrides: dict[str, str]) -> tuple[str, Path | None]:
    try:
        relative_parent = path.parent.relative_to(root)
    except ValueError:
        return "auto", None

    candidates = [relative_parent, *relative_parent.parents]
    for candidate in candidates:
        key = "." if str(candidate) == "." else candidate.as_posix()
        category = category_overrides.get(key)
        if category and category != "auto":
            category_folder = root if key == "." else root / candidate
            return category, category_folder
    return "auto", None


def forced_series_title(path: Path, category_folder: Path) -> str:
    if path.parent == category_folder:
        return parent_series_title(path)
    return clean_title(category_folder.name)
