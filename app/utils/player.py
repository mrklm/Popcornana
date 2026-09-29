from __future__ import annotations

import os
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
    """Select only an exact basename or an explicit French suffix.

    The video basename is case-sensitive; language markers and extensions are
    case-insensitive. French wins over an untagged match, then extension order
    and filename order break ties deterministically.
    """
    matches = []
    for candidate in media_path.parent.iterdir():
        extension = candidate.suffix.casefold()
        if extension not in SUBTITLE_EXTENSIONS or not candidate.is_file():
            continue
        if candidate.stem == media_path.stem:
            priority = 1
        elif candidate.stem.startswith(media_path.stem):
            suffix = candidate.stem[len(media_path.stem):].casefold()
            if suffix not in (".fr", "-fr", "_fr", ".french", "-french", "_french"):
                continue
            priority = 0
        else:
            continue
        matches.append((priority, SUBTITLE_EXTENSIONS.index(extension), candidate.name, candidate))
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
