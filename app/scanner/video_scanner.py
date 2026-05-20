from __future__ import annotations

from pathlib import Path

from app.models.media import MediaItem
from app.scanner.name_cleaner import is_video_file, parse_media_filename


def scan_videos(folder: str | Path) -> list[MediaItem]:
    root = Path(folder).expanduser()
    if not root.exists():
        return []

    items: list[MediaItem] = []
    for path in sorted(root.rglob("*")):
        if not is_video_file(path):
            continue
        parsed = parse_media_filename(path)
        items.append(
            MediaItem(
                filepath=path,
                media_type=str(parsed["media_type"]),
                title=str(parsed["title"]),
                year=parsed["year"] if isinstance(parsed["year"], int) else None,
                season=parsed["season"] if isinstance(parsed["season"], int) else None,
                episode=parsed["episode"] if isinstance(parsed["episode"], int) else None,
            )
        )
    return items
