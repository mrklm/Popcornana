"""Linux packaging checks for the Qt desktop platform plugins."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

# Client libraries, not the host's glibc, graphics driver or display server.
CLIENT_LIBRARY = re.compile(r'^lib(?:xcb(?:-[\w-]+)?|X11(?:-xcb)?|Xau|Xdmcp|xkbcommon(?:-x11)?|wayland-[\w-]+)\.so')


def linked_libraries(binary: Path, search: list[Path] = ()) -> dict[str, Path]:
    env = os.environ.copy()
    env['LC_ALL'] = 'C'
    env['LD_LIBRARY_PATH'] = ':'.join(map(str, search))
    result = subprocess.run(['ldd', str(binary)], env=env, capture_output=True, text=True, check=True)
    if 'not found' in result.stdout:
        missing = [line.strip() for line in result.stdout.splitlines() if 'not found' in line]
        raise RuntimeError(f'Missing Qt dependencies for {binary}: {missing}. Install the Linux build packages documented in README.md.')
    libraries = {}
    for line in result.stdout.splitlines():
        match = re.match(r'\s*(\S+) => (.+?) \(0x[0-9a-f]+\)', line)
        if match:
            libraries[match[1]] = Path(match[2])
    return libraries


def collect_linux_qt_dependencies() -> dict[str, Path]:
    from PySide6.QtCore import QLibraryInfo
    plugins = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath))
    roots = [plugins / 'platforms/libqxcb.so', plugins / 'platforms/libqwayland.so']
    # Include optional integrations that Qt can load dynamically.
    for group in ('xcbglintegrations', 'wayland-graphics-integration-client',
                  'wayland-shell-integration', 'wayland-decoration-client'):
        roots.extend(sorted((plugins / group).glob('*.so')))
    clients = {}
    for binary in roots:
        if not binary.is_file():
            raise RuntimeError(f'Required Qt plugin missing: {binary}')
        for name, path in linked_libraries(binary).items():
            if CLIENT_LIBRARY.match(name):
                clients[name] = path
    if 'libxcb-cursor.so.0' not in clients:
        raise RuntimeError('Qt XCB cursor dependency was not found; refusing an incomplete Linux build.')
    return clients


def verify_linux_archive(executable: Path, required: dict[str, Path], destination: Path) -> None:
    """Inspect the actual onefile payload; ldd on the bootloader is insufficient."""
    from PyInstaller.archive.readers import CArchiveReader
    archive = CArchiveReader(str(executable))
    missing = set(required) - archive.toc.keys()
    if missing:
        raise RuntimeError(f'Linux archive lacks required client libraries: {sorted(missing)}')
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    # Extract ELF libraries without running the application, for dependency inspection.
    for name, entry in archive.toc.items():
        if entry[-1] != 'b' or '.so' not in name:
            continue
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.extract(name))
    roots = [destination / 'PySide6/Qt/plugins/platforms' / name
             for name in ('libqxcb.so', 'libqwayland.so')]
    for group in ('xcbglintegrations', 'wayland-graphics-integration-client',
                  'wayland-shell-integration', 'wayland-decoration-client'):
        roots.extend(sorted((destination / 'PySide6/Qt/plugins' / group).glob('*.so')))
    report = []
    for plugin in roots:
        if not plugin.is_file():
            raise RuntimeError(f'Platform plugin absent from archive: {plugin.name}')
        libs = linked_libraries(plugin, [destination, destination / 'PySide6/Qt/lib'])
        for name, path in libs.items():
            if (CLIENT_LIBRARY.match(name) or name.startswith('libQt6')) and not path.resolve().is_relative_to(destination.resolve()):
                raise RuntimeError(f'{plugin.name} still relies on host client library {name}: {path}')
        report.append(plugin.name + '\n' + '\n'.join(f'  {name}: {path}' for name, path in sorted(libs.items())))
    (destination / 'dependency-report.txt').write_text('\n\n'.join(report))
