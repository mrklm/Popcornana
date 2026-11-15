"""Comparaison de deux sources : rapprochement des vidéos par taille exacte et harmonisation.

Règles de sécurité : aucune suppression, aucune copie ni déplacement de vidéo. Les seules
opérations sont des renommages sur place, des copies de petits fichiers (sous-titres, cover,
Popinfo.txt) et la mise de côté en ``.bak`` d'un fichier remplacé. Chaque opération est
journalisée pour pouvoir être annulée.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from app.scanner.name_cleaner import is_video_file, parse_media_filename
from app.utils.player import SUBTITLE_EXTENSIONS

PORTABLE_INFO_FILENAME = "Popinfo.txt"
COVER_STEM = "cover"
COVER_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
FORBIDDEN_NAME_CHARS = set('/\\:*?"<>|')
SIDES = ("left", "right")
JOURNAL_LIMIT = 20

FR_MARKERS = {"fr", "fre", "fra", "french", "francais", "français", "vf", "vff"}
EN_MARKERS = {"en", "eng", "english", "anglais", "vo"}


@dataclass
class SideFiles:
    root: Path
    video: Path
    subtitles: dict[str, Path]
    cover: Path | None
    popinfo: Path | None

    @property
    def folder(self) -> Path:
        return self.video.parent

    @property
    def folder_renamable(self) -> bool:
        return self.folder != self.root


@dataclass
class Choice:
    side: str
    name: str


class ConflictError(Exception):
    pass


def subtitle_language(path: Path) -> str:
    markers = set(re.split(r"[\W_]+", path.stem.casefold()))
    if markers & FR_MARKERS:
        return "fr"
    if markers & EN_MARKERS:
        return "en"
    return ""


def collect_side(root: Path, video: Path) -> SideFiles:
    subtitles: dict[str, Path] = {}
    cover = None
    popinfo = None
    candidates = sorted((p for p in video.parent.iterdir() if p.is_file()), key=lambda p: (p.name.casefold(), p.name))
    for candidate in candidates:
        suffix = candidate.suffix.lower()
        if suffix in SUBTITLE_EXTENSIONS:
            subtitles.setdefault(subtitle_language(candidate), candidate)
        elif cover is None and candidate.stem.casefold() == COVER_STEM and suffix in COVER_EXTENSIONS:
            cover = candidate
        elif candidate.name == PORTABLE_INFO_FILENAME:
            popinfo = candidate
    return SideFiles(root=root, video=video, subtitles=subtitles, cover=cover, popinfo=popinfo)


def align_subtitles(left: SideFiles, right: SideFiles) -> None:
    """Un seul sous-titre de chaque côté : ils sont comparés face à face, même si un seul indique sa langue."""
    if len(left.subtitles) == 1 and len(right.subtitles) == 1 and set(left.subtitles) != set(right.subtitles):
        key = next(k for k in (*left.subtitles, *right.subtitles) if k)
        left.subtitles = {key: next(iter(left.subtitles.values()))}
        right.subtitles = {key: next(iter(right.subtitles.values()))}


def collect_pair(left_root: Path, left_video: Path, right_root: Path, right_video: Path) -> dict[str, SideFiles]:
    left, right = collect_side(left_root, left_video), collect_side(right_root, right_video)
    align_subtitles(left, right)
    return {"left": left, "right": right}


def _videos_by_size(root: Path, should_stop: Callable[[], bool] | None = None) -> dict[int, list[Path]]:
    by_folder: dict[Path, list[Path]] = {}
    for current, directories, files in os.walk(root):
        if should_stop and should_stop():
            break
        directories[:] = [d for d in directories if not d.startswith(".")]
        for name in files:
            path = Path(current) / name
            if is_video_file(path):
                by_folder.setdefault(path.parent, []).append(path)
    sizes: dict[int, list[Path]] = {}
    for folder, videos in by_folder.items():
        # Les séries et les dossiers à plusieurs vidéos sont exclus pour l'instant.
        if len(videos) != 1 or parse_media_filename(videos[0])["media_type"] == "tv":
            continue
        try:
            size = videos[0].stat().st_size
        except OSError:
            continue
        sizes.setdefault(size, []).append(videos[0])
    return sizes


def find_pairs(left_root: Path, right_root: Path, should_stop: Callable[[], bool] | None = None) -> tuple[list[tuple[Path, Path]], int]:
    """Associe les vidéos de taille identique à l'octet près. Renvoie (paires, tailles ambiguës)."""
    left = _videos_by_size(left_root, should_stop)
    right = _videos_by_size(right_root, should_stop)
    pairs = []
    ambiguous = 0
    for size in set(left) & set(right):
        if len(left[size]) != 1 or len(right[size]) != 1:
            ambiguous += 1
            continue
        if left[size][0].resolve() != right[size][0].resolve():
            pairs.append((left[size][0], right[size][0]))
    pairs.sort(key=lambda pair: (str(pair[0]).casefold(), str(pair[0])))
    return pairs, ambiguous


def same_content(first: Path | None, second: Path | None) -> bool:
    if first is None or second is None:
        return first is second
    try:
        return first.stat().st_size == second.stat().st_size and first.read_bytes() == second.read_bytes()
    except OSError:
        return False


def same_name(first: str, second: str) -> bool:
    return unicodedata.normalize("NFC", first) == unicodedata.normalize("NFC", second)


def row_keys(left: SideFiles, right: SideFiles) -> list[str]:
    keys = ["video", "folder"]
    languages = sorted(set(left.subtitles) | set(right.subtitles), key=lambda key: ({"fr": 0, "en": 1}.get(key, 2), key))
    keys.extend("sub:" + language for language in languages)
    keys.append("cover")
    return keys


def row_files(side: SideFiles, key: str) -> Path | None:
    if key == "video":
        return side.video
    if key == "folder":
        return side.folder
    if key == "cover":
        return side.cover
    return side.subtitles.get(key[4:])


def row_identical(left: SideFiles, right: SideFiles, key: str) -> bool:
    first, second = row_files(left, key), row_files(right, key)
    if key == "folder":
        return same_name(first.name, second.name) or not (left.folder_renamable and right.folder_renamable)
    if first is None or second is None:
        return first is second
    if not same_name(first.name, second.name):
        return False
    return key == "video" or same_content(first, second)


def pair_is_identical(left: SideFiles, right: SideFiles) -> bool:
    return all(row_identical(left, right, key) for key in row_keys(left, right))


def editable_name(path: Path, key: str) -> str:
    """Partie modifiable d'un nom : l'extension des fichiers est conservée."""
    return path.name if key == "folder" else path.stem


def validate_name(name: str) -> str | None:
    if not name or not name.strip():
        return "Le nom ne peut pas être vide."
    if name != name.strip() or name.endswith("."):
        return "Le nom ne doit pas commencer ou finir par un espace, ni finir par un point."
    if name in {".", ".."} or name.startswith("."):
        return "Le nom ne doit pas commencer par un point."
    forbidden = sorted(FORBIDDEN_NAME_CHARS & set(name))
    if forbidden:
        return "Caractères interdits : " + " ".join(forbidden)
    if any(ord(char) < 32 for char in name):
        return "Le nom contient des caractères de contrôle."
    return None


def _backup_path(path: Path, stamp: str) -> Path:
    candidate = path.with_name(path.name + ".bak")
    if not candidate.exists():
        return candidate
    return path.with_name(f"{path.name}.{stamp}.bak")


def _popinfo_text_for(source: Path, video_name: str) -> bytes:
    text = source.read_text(encoding="utf-8")
    header, separator, synopsis = text.partition("\nsynopsis:")
    header = re.sub(r"(?m)^file:.*$", lambda _match: "file: " + video_name, header)
    return (header + separator + synopsis).encode("utf-8")


def build_operations(sides: dict[str, SideFiles], choices: dict[str, Choice]) -> list[dict]:
    """Prépare la liste ordonnée des opérations, sans rien modifier sur le disque.

    Ordre : copies et mises de côté (depuis les chemins d'origine), puis renommages des fichiers,
    puis renommage des dossiers en dernier.
    """
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    copies: list[dict] = []
    renames: list[dict] = []
    folders: list[dict] = []

    def replace_with(target: Path, existing: Path | None, source: Path | None = None, content: bytes | None = None) -> None:
        if existing is not None:
            copies.append({"op": "aside", "src": str(existing), "dst": str(_backup_path(existing, stamp))})
        if content is not None:
            copies.append({"op": "write", "dst": str(target), "content": content})
        else:
            copies.append({"op": "copy", "src": str(source), "dst": str(target)})

    for key, choice in choices.items():
        if not key.startswith("sub:"):
            continue
        chosen = sides[choice.side].subtitles.get(key[4:])
        if chosen is None:
            continue
        for side_name, side in sides.items():
            target = side.folder / (choice.name + chosen.suffix)
            existing = side.subtitles.get(key[4:])
            if side_name == choice.side:
                if not same_name(chosen.name, target.name):
                    renames.append({"op": "rename", "src": str(chosen), "dst": str(target)})
            elif existing is not None and same_name(existing.name, target.name) and same_content(existing, chosen):
                continue
            else:
                replace_with(target, existing, source=chosen)

    video_choice = choices.get("video")
    final_video_names = {
        name: (video_choice.name + side.video.suffix if video_choice else side.video.name)
        for name, side in sides.items()
    }

    cover_choice = choices.get("cover")
    popinfo_written: set[str] = set()
    if cover_choice is not None:
        chosen_side = sides[cover_choice.side]
        if chosen_side.cover is not None:
            for side_name, side in sides.items():
                if side_name == cover_choice.side:
                    continue
                target = side.folder / chosen_side.cover.name
                if not (side.cover is not None and same_name(side.cover.name, target.name) and same_content(side.cover, chosen_side.cover)):
                    replace_with(target, side.cover, source=chosen_side.cover)
                if chosen_side.popinfo is not None:
                    content = _popinfo_text_for(chosen_side.popinfo, final_video_names[side_name])
                    if side.popinfo is None or side.popinfo.read_bytes() != content:
                        replace_with(side.folder / PORTABLE_INFO_FILENAME, side.popinfo, content=content)
                    popinfo_written.add(side_name)

    if video_choice is not None:
        for side_name, side in sides.items():
            target = side.video.with_name(final_video_names[side_name])
            if not same_name(side.video.name, target.name):
                renames.append({"op": "rename", "src": str(side.video), "dst": str(target)})
            # Le champ « file: » du Popinfo.txt doit suivre le nouveau nom de la vidéo.
            if side_name not in popinfo_written and side.popinfo is not None:
                content = _popinfo_text_for(side.popinfo, final_video_names[side_name])
                if side.popinfo.read_bytes() != content:
                    replace_with(side.popinfo, side.popinfo, content=content)

    folder_choice = choices.get("folder")
    if folder_choice is not None:
        for side in sides.values():
            if not side.folder_renamable:
                continue
            target = side.folder.with_name(folder_choice.name)
            if not same_name(side.folder.name, target.name):
                folders.append({"op": "rename", "src": str(side.folder), "dst": str(target)})

    return copies + renames + folders


def _is_case_only_rename(src: Path, dst: Path) -> bool:
    try:
        return dst.exists() and os.path.samefile(src, dst)
    except OSError:
        return False


def check_conflicts(operations: list[dict]) -> list[str]:
    """Simule les opérations et renvoie les cibles déjà occupées."""
    freed: set[str] = set()
    created: set[str] = set()
    conflicts = []

    def occupied(path: str) -> bool:
        return path in created or (os.path.lexists(path) and path not in freed)

    for operation in operations:
        dst = operation["dst"]
        if operation["op"] == "rename":
            if occupied(dst) and not _is_case_only_rename(Path(operation["src"]), Path(dst)):
                conflicts.append(dst)
            freed.add(operation["src"])
        elif operation["op"] == "aside":
            if occupied(dst):
                conflicts.append(dst)
            freed.add(operation["src"])
        elif occupied(dst):
            conflicts.append(dst)
        created.add(dst)
        freed.discard(dst)
    return conflicts


def _rename(src: Path, dst: Path) -> None:
    if _is_case_only_rename(src, dst) and src.name != dst.name:
        # Disque insensible à la casse : passage par un nom temporaire.
        temporary = src.with_name(f".{src.name}.popcornana-tmp")
        os.rename(src, temporary)
        os.rename(temporary, dst)
        return
    if os.path.lexists(dst):
        raise ConflictError(str(dst))
    os.rename(src, dst)


def _write_new(target: Path, writer: Callable[[Path], None]) -> None:
    if os.path.lexists(target):
        raise ConflictError(str(target))
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    os.close(descriptor)
    staged = Path(temporary)
    try:
        writer(staged)
        os.replace(staged, target)
    finally:
        if staged.exists():
            staged.unlink()


def apply_operations(operations: list[dict]) -> tuple[list[dict], str | None]:
    """Applique les opérations dans l'ordre. Renvoie (opérations faites, erreur éventuelle)."""
    done: list[dict] = []
    for operation in operations:
        dst = Path(operation["dst"])
        try:
            if operation["op"] in ("rename", "aside"):
                _rename(Path(operation["src"]), dst)
            elif operation["op"] == "copy":
                _write_new(dst, lambda staged, source=operation["src"]: shutil.copyfile(source, staged))
            elif operation["op"] == "write":
                _write_new(dst, lambda staged, content=operation["content"]: staged.write_bytes(content))
        except (OSError, ConflictError) as error:
            return done, f"{dst} : {error}"
        done.append({key: value for key, value in operation.items() if key != "content"})
    return done, None


def undo_operations(operations: list[dict]) -> list[str]:
    """Annule des opérations faites, dans l'ordre inverse. Renvoie les échecs."""
    failures: list[str] = []
    for operation in reversed(operations):
        dst = Path(operation["dst"])
        try:
            if operation["op"] in ("rename", "aside"):
                if not dst.exists():
                    raise FileNotFoundError(str(dst))
                _rename(dst, Path(operation["src"]))
            elif dst.exists():
                # Fichier créé par l'harmonisation : l'ancien a été remis en place juste après.
                dst.unlink()
        except (OSError, ConflictError) as error:
            failures.append(f"{dst} : {error}")
    return failures


def database_renames(operations: list[dict]) -> list[tuple[str, str]]:
    """Chemins à reporter dans la base : renommages, et cover remplacée par une autre extension."""
    renames = [(op["src"], op["dst"]) for op in operations if op["op"] == "rename"]
    asides = {Path(op["src"]).parent: op["src"] for op in operations
              if op["op"] == "aside" and Path(op["src"]).stem.casefold() == COVER_STEM}
    for op in operations:
        if op["op"] != "copy" or Path(op["dst"]).stem.casefold() != COVER_STEM:
            continue
        previous = asides.get(Path(op["dst"]).parent)
        if previous and previous != op["dst"]:
            renames.insert(0, (previous, op["dst"]))
    return renames


def load_journal(path: Path) -> list[dict]:
    try:
        sessions = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return sessions if isinstance(sessions, list) else []


def save_journal(path: Path, sessions: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(sessions[-JOURNAL_LIMIT:], ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(temporary, path)


def new_session(left_root: Path, right_root: Path) -> dict:
    return {
        "date": datetime.now(timezone.utc).isoformat(),
        "left": str(left_root),
        "right": str(right_root),
        "operations": [],
    }


def format_size(size: int) -> str:
    for unit, factor in (("Go", 1024 ** 3), ("Mo", 1024 ** 2), ("Ko", 1024)):
        if size >= factor:
            return f"{size / factor:.2f} {unit}".replace(".", ",")
    return f"{size} o"
