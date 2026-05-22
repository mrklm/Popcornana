from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


SUBTITLE_EXTENSIONS = (".srt", ".ass", ".ssa", ".sub", ".vtt")


def open_media(path: str | Path) -> None:
    media_path = Path(path)
    subtitle_path = find_subtitle(media_path)
    vlc_path = find_vlc()
    if vlc_path:
        command = [vlc_path, "--fullscreen", str(media_path)]
        if subtitle_path:
            command.extend(["--sub-file", str(subtitle_path)])
        subprocess.Popen(command)
        return

    if sys.platform == "darwin":
        subprocess.Popen(["open", str(media_path)])
    elif os.name == "nt":
        os.startfile(str(media_path))  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", str(media_path)])


def find_subtitle(media_path: Path) -> Path | None:
    exact_matches = [media_path.with_suffix(extension) for extension in SUBTITLE_EXTENSIONS]
    for candidate in exact_matches:
        if candidate.exists():
            return candidate

    for candidate in sorted(media_path.parent.iterdir()):
        if candidate.suffix.casefold() in SUBTITLE_EXTENSIONS:
            return candidate
    return None


def find_vlc() -> str | None:
    if sys.platform == "darwin":
        macos_vlc = Path("/Applications/VLC.app/Contents/MacOS/VLC")
        if macos_vlc.exists():
            return str(macos_vlc)
    if os.name == "nt":
        for candidate in windows_vlc_candidates():
            if candidate.exists():
                return str(candidate)
    return shutil.which("vlc") or shutil.which("VLC")


def windows_vlc_candidates() -> list[Path]:
    candidates: list[Path] = []
    for env_var in ("ProgramW6432", "PROGRAMFILES", "PROGRAMFILES(X86)"):
        base_dir = os.getenv(env_var)
        if not base_dir:
            continue
        candidates.append(Path(base_dir) / "VideoLAN" / "VLC" / "vlc.exe")
    return candidates
