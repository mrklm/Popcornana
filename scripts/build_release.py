from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Popcornana release artifact for the current OS.")
    parser.add_argument("--target", required=True, choices=["macos-intel", "windows-x64", "linux-x64"])
    args = parser.parse_args()

    validate_target(args.target)
    clean_build_dirs()
    run_pyinstaller(args.target)
    package_artifact(args.target)


def validate_target(target: str) -> None:
    current_targets = {
        "darwin": "macos-intel",
        "win32": "windows-x64",
        "linux": "linux-x64",
    }
    expected = current_targets.get(sys.platform)
    if expected != target:
        raise SystemExit(f"Target {target!r} must be built on {expected or sys.platform!r}.")


def clean_build_dirs() -> None:
    shutil.rmtree(DIST_DIR, ignore_errors=True)
    shutil.rmtree(BUILD_DIR, ignore_errors=True)


def run_pyinstaller(target: str) -> None:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "Popcornana",
        "--add-data",
        add_data_arg("assets", "assets"),
        "--add-data",
        add_data_arg(".env.example", "."),
        "main.py",
    ]
    if target in {"windows-x64", "linux-x64"}:
        command.insert(command.index("--windowed") + 1, "--onefile")

    subprocess.run(command, cwd=ROOT_DIR, check=True)


def add_data_arg(source: str, destination: str) -> str:
    separator = ";" if sys.platform == "win32" else ":"
    return f"{source}{separator}{destination}"


def package_artifact(target: str) -> None:
    artifact_base = DIST_DIR / f"Popcornana-{target}"
    if target == "macos-intel":
        app_path = DIST_DIR / "Popcornana.app"
        zip_path = artifact_base.with_suffix(".zip")
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
