"""Find unused cached images without visiting media sources or following symlinks."""
import os
from pathlib import Path

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}


def unused_images(cache: Path, references: list[str | None]) -> dict[Path, tuple[int, int, int, int]]:
    if cache.is_symlink() or not cache.is_dir():
        return {}
    root = cache.resolve()
    used = set()
    for value in references:
        if not value or value.startswith(('http://', 'https://')):
            continue
        path = Path(value)
        # TMDb paths may start with /, while portable posters use absolute paths.
        used.add((root / value.lstrip('/')).resolve())
        if path.is_absolute():
            used.add(path.resolve())
    candidates = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if not (Path(directory) / name).is_symlink()]
        for name in files:
            path = Path(directory) / name
            if path.suffix.lower() not in IMAGE_EXTENSIONS or path.is_symlink():
                continue
            if path.resolve() in used:
                continue
            info = path.stat()
            candidates[path] = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
    return candidates


def remove_unused_images(cache: Path, references: list[str | None], preview: dict) -> tuple[int, int, int]:
    # Recheck references and file identity after the confirmation dialog.
    current = unused_images(cache, references)
    removed = size = failed = 0
    for path, identity in preview.items():
        if current.get(path) != identity:
            continue
        try:
            if path.is_symlink() or path.resolve() != path:
                continue
            info = path.stat()
            if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) != identity:
                continue
            path.unlink()
            removed += 1
            size += identity[2]
        except OSError:
            failed += 1
    return removed, size, failed
