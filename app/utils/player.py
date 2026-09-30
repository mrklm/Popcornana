from __future__ import annotations

import os
import re
import shutil
import subprocess
import platform
from pathlib import Path


SUBTITLE_EXTENSIONS = (".srt", ".ass", ".ssa", ".sub", ".vtt")


# Keep automatic priorities separate from detection and launch commands.
AUTO_PRIORITIES = {
    "Linux": ("mpv", "vlc"),
    "Darwin": ("vlc",),
    "Windows": ("vlc",),
}
PLAYER_LABELS = {"auto": "Automatique", "mpv": "MPV", "vlc": "VLC", "system": "Lecteur système"}


def detect_players() -> dict[str, str]:
    return {name: executable for name, executable in
            (("mpv", find_mpv()), ("vlc", find_vlc())) if executable}


def get_available_players() -> list[str]:
    return ["auto", *detect_players(), "system"]


def get_preferred_player(preference: str | None = None,
                         players: dict[str, str] | None = None) -> str:
    if players is None:
        players = detect_players()
    if preference in (None, "auto"):
        return next((name for name in AUTO_PRIORITIES.get(platform.system(), ())
                     if name in players), "system")
    return preference if preference in players else "system"


def open_media(path: str | Path, preference: str | None = None) -> None:
    # Absolute paths also keep filenames beginning with '-' from becoming options.
    media_path = Path(path).absolute()
    players = detect_players()
    selected = get_preferred_player(preference, players)
    if selected != "system":
        subtitle_path = find_subtitle(media_path)
        if selected == "mpv":
            command = [players[selected], "--fullscreen"]
            if subtitle_path:
                command.append("--sub-file=" + str(subtitle_path))
            command.append(str(media_path))
        else:
            command = [players[selected], "--fullscreen", str(media_path)]
            if subtitle_path:
                command.extend(["--sub-file", str(subtitle_path)])
        try:
            subprocess.Popen(command)
            return
        except OSError:
            # The executable may have disappeared or lack permission to run.
            pass

    system = platform.system()
    if system == "Darwin":
        subprocess.Popen(["open", str(media_path)])
    elif system == "Windows":
        os.startfile(str(media_path))  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", str(media_path)])


def find_subtitle(media_path: Path) -> Path | None:
    """Prefer French, then English, then any subtitle in the video folder.

    Language markers are whole tokens, ignoring case. Ties use case-insensitive
    filename order, with the original filename as a deterministic tie-breaker.
    """
    matches = []
    for candidate in media_path.parent.iterdir():
        if candidate.suffix.casefold() not in SUBTITLE_EXTENSIONS or not candidate.is_file():
            continue
        # Underscores, punctuation and spaces separate markers; letters and
        # digits stay together so words such as "friends" cannot match "fr".
        markers = set(re.split(r"[\W_]+", candidate.stem.casefold()))
        if markers & {"fr", "french", "francais", "français"}:
            priority = 0
        elif markers & {"en", "eng", "english", "anglais"}:
            priority = 1
        else:
            priority = 2
        matches.append((priority, candidate.name.casefold(), candidate.name, candidate))
    return min(matches)[-1] if matches else None


def find_vlc() -> str | None:
    if platform.system() == "Darwin":
        macos_vlc = Path("/Applications/VLC.app/Contents/MacOS/VLC")
        if macos_vlc.is_file() and os.access(macos_vlc, os.X_OK):
            return str(macos_vlc)
    if platform.system() == "Windows":
        for candidate in windows_vlc_candidates():
            if candidate.is_file() and os.access(candidate, os.X_OK):
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


def find_mpv() -> str | None:
    executable = shutil.which("mpv")
    if executable:
        return executable
    candidates: list[Path] = []
    if platform.system() == "Darwin":
        candidates = [Path("/Applications/mpv.app/Contents/MacOS/mpv"),
                      Path.home() / "Applications/mpv.app/Contents/MacOS/mpv",
                      Path("/opt/homebrew/bin/mpv"), Path("/usr/local/bin/mpv")]
    elif platform.system() == "Windows":
        candidates = [Path(base) / "mpv" / "mpv.exe"
                      for key in ("ProgramW6432", "PROGRAMFILES", "PROGRAMFILES(X86)")
                      for base in [os.getenv(key)] if base]
    return next((str(path) for path in candidates
                 if path.is_file() and os.access(path, os.X_OK)), None)
