from __future__ import annotations

from pathlib import Path

from app.models.media import MediaItem
from app.scanner.name_cleaner import clean_title, is_video_file, parse_media_filename


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
            season = None
            episode = None
        elif category == "tv":
            media_type = "tv"
            title = clean_title(category_folder.name) if category_folder else title
        items.append(
            MediaItem(
                filepath=path,
                media_type=media_type,
                title=title,
                year=parsed["year"] if isinstance(parsed["year"], int) else None,
                season=season,
                episode=episode,
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
