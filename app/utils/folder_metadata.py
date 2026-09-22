"""Portable folder metadata, kept separate from the movies in the same folder."""

import json
import shutil
from pathlib import Path


COVER_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


def read_folder_description(folder: Path) -> str:
    try:
        text = (folder / "Popinfo.txt").read_text(encoding="utf-8")
    except OSError:
        return ""
    for line in text.splitlines():
        if line == "synopsis:":
            break
        if line.startswith("folder_description:"):
            value = line.partition(":")[2].strip()
            try:
                decoded = json.loads(value)
            except ValueError:
                return value
            return decoded if isinstance(decoded, str) else ""
    return ""


def write_folder_description(folder: Path, description: str) -> None:
    path = folder / "Popinfo.txt"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    # Only replace our header. Everything from synopsis onward belongs to the film.
    lines = text.splitlines(keepends=True)
    header_end = next((i for i, line in enumerate(lines) if line.rstrip("\r\n") == "synopsis:"), len(lines))
    preserved = [line for line in lines[:header_end] if not line.startswith("folder_description:")]
    preserved.extend(lines[header_end:])
    header = "folder_description: " + json.dumps(description, ensure_ascii=False) + "\n"
    path.write_text(header + "".join(preserved), encoding="utf-8")


def folder_cover(folder: Path) -> Path | None:
    return next((folder / ("repocover" + ext) for ext in COVER_EXTENSIONS
                 if (folder / ("repocover" + ext)).is_file()), None)


def write_folder_cover(folder: Path, source: Path) -> Path:
    extension = source.suffix.lower()
    if extension not in COVER_EXTENSIONS:
        raise ValueError("Format de visuel non pris en charge.")
    target = folder / ("repocover" + extension)
    if source.resolve() != target.resolve():
        shutil.copyfile(source, target)
    for ext in COVER_EXTENSIONS:
        previous = folder / ("repocover" + ext)
        if previous != target and previous.exists():
            previous.unlink()
    return target
