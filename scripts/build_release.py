from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

from PIL import Image


ROOT_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
ICON_SOURCE = ROOT_DIR / "assets" / "popcornana_ico.png"
ICON_DIR = BUILD_DIR / "icons"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Popcornana release artifact for the current OS.")
    parser.add_argument(
        "--target",
        required=True,
        choices=["macos-intel", "macos-catalina-intel", "windows-x64", "linux-x64"],
    )
    args = parser.parse_args()

    validate_target(args.target)
    clean_build_dirs()
    icon_path = prepare_icon(args.target)
    run_pyinstaller(args.target, icon_path)
    package_artifact(args.target)


def validate_target(target: str) -> None:
    current_targets = {
        "darwin": {"macos-intel", "macos-catalina-intel"},
        "win32": "windows-x64",
        "linux": "linux-x64",
    }
    expected = current_targets.get(sys.platform)
    if isinstance(expected, set) and target in expected:
        return
    if expected != target:
        raise SystemExit(f"Target {target!r} must be built on {expected or sys.platform!r}.")


def clean_build_dirs() -> None:
    shutil.rmtree(DIST_DIR, ignore_errors=True)
    shutil.rmtree(BUILD_DIR, ignore_errors=True)


def prepare_icon(target: str) -> Path:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    if target == "windows-x64":
        icon_path = ICON_DIR / "popcornana.ico"
        image = Image.open(ICON_SOURCE).convert("RGBA")
        image.save(icon_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        return icon_path
    if target in {"macos-intel", "macos-catalina-intel"}:
        icon_path = ICON_DIR / "popcornana.icns"
        image = Image.open(ICON_SOURCE).convert("RGBA")
        image.save(icon_path)
        return icon_path
    return ICON_SOURCE


def run_pyinstaller(target: str, icon_path: Path) -> None:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "Popcornana",
        "--icon",
        str(icon_path),
        "--add-data",
        add_data_arg("assets", "assets"),
        "--add-data",
        add_data_arg(".env.example", "."),
        "main.py",
    ]
    if target in {"windows-x64", "linux-x64"}:
        command.insert(command.index("--windowed") + 1, "--onefile")
    if target in {"macos-intel", "macos-catalina-intel"}:
        command.extend(["--target-architecture", "x86_64"])

    env = os.environ.copy()
    env["PYINSTALLER_CONFIG_DIR"] = str(BUILD_DIR / "pyinstaller-config")
    if target == "macos-catalina-intel":
        env["MACOSX_DEPLOYMENT_TARGET"] = "10.15"
    subprocess.run(command, cwd=ROOT_DIR, env=env, check=True)


def add_data_arg(source: str, destination: str) -> str:
    separator = ";" if sys.platform == "win32" else ":"
    return f"{source}{separator}{destination}"


def package_artifact(target: str) -> None:
    artifact_base = DIST_DIR / f"Popcornana-{target}"
    if target in {"macos-intel", "macos-catalina-intel"}:
        app_path = DIST_DIR / "Popcornana.app"
        zip_path = artifact_base.with_suffix(".zip")
        if shutil.which("ditto"):
            subprocess.run(
                ["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(app_path), str(zip_path)],
                check=True,
            )
            print(zip_path)
            return
        zip_directory(app_path, zip_path)
        print(zip_path)
        return

    if target == "windows-x64":
        exe_path = DIST_DIR / "Popcornana.exe"
        zip_path = artifact_base.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(exe_path, exe_path.name)
        print(zip_path)
        return

    executable_path = DIST_DIR / "Popcornana"
    tar_path = artifact_base.with_suffix(".tar.gz")
    with tarfile.open(tar_path, "w:gz") as archive:
        archive.add(executable_path, arcname=executable_path.name)
    print(tar_path)


def zip_directory(source: Path, target: Path) -> None:
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in source.rglob("*"):
            archive.write(path, source.name / path.relative_to(source))


if __name__ == "__main__":
    main()
