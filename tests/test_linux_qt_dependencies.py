import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.linux_qt_dependencies import CLIENT_LIBRARY, linked_libraries, verify_linux_archive


class LinuxQtDependencyTests(unittest.TestCase):
    def test_paths_with_spaces(self):
        result = subprocess.CompletedProcess([], 0, 'libQt6Core.so.6 => /path with spaces/libQt6Core.so.6 (0xabc)\nlibxcb.so.1 => /lib/libxcb.so.1 (0x123)\n', '')
        with patch('scripts.linux_qt_dependencies.subprocess.run', return_value=result):
            libs = linked_libraries(Path('/plugin.so'))
        self.assertEqual(libs['libQt6Core.so.6'], Path('/path with spaces/libQt6Core.so.6'))

    def test_missing_transitive_dependency_fails(self):
        result = subprocess.CompletedProcess([], 0, 'libxcb-cursor.so.0 => not found\n', '')
        with patch('scripts.linux_qt_dependencies.subprocess.run', return_value=result):
            with self.assertRaisesRegex(RuntimeError, 'libxcb-cursor'):
                linked_libraries(Path('/plugin.so'))

    def test_client_scope_excludes_host_runtime_and_drivers(self):
        for name in ('libxcb.so.1', 'libxcb-cursor.so.0', 'libX11.so.6', 'libXau.so.6', 'libxkbcommon-x11.so.0', 'libwayland-client.so.0'):
            self.assertIsNotNone(CLIENT_LIBRARY.match(name))
        for name in ('libc.so.6', 'libpthread.so.0', 'libGL.so.1', 'libEGL.so.1', 'libdrm.so.2'):
            self.assertIsNone(CLIENT_LIBRARY.match(name))

    def test_archive_cannot_omit_required_library(self):
        with patch('PyInstaller.archive.readers.CArchiveReader') as reader:
            reader.return_value.toc = {}
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaisesRegex(RuntimeError, 'libxcb-cursor'):
                    verify_linux_archive(Path('app'), {'libxcb-cursor.so.0': Path('/lib/cursor')}, Path(tmp))
