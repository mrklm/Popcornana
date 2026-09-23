import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.models.media import MediaItem
from app.ui.main_window import create_portable_metadata_files, write_source_marker, parse_portable_info
from app.utils.safe_files import atomic_write
from app.utils.folder_metadata import write_folder_description, read_folder_description


class PortableSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        video = self.folder / 'film.mkv'
        video.touch()
        self.poster = self.folder / 'cached.png'
        self.poster.write_bytes(b'new image')
        self.item = MediaItem(video, 'movie', 'Film', year=2025, overview='Résumé', poster_path=str(self.poster))

    def test_disabled_even_for_manual_edit(self):
        self.assertEqual(create_portable_metadata_files(self.item, force=True, update=True, replace_cover=True), 0)
        self.assertFalse((self.folder / 'Popinfo.txt').exists())
        self.assertFalse((self.folder / 'cover.png').exists())

    def test_export_and_manual_update_with_backup(self):
        write_source_marker(self.folder, True)
        self.assertEqual(create_portable_metadata_files(self.item, force=True), 2)
        write_folder_description(self.folder, 'Présentation du dossier')
        info = self.folder / 'Popinfo.txt'
        original = info.read_bytes()
        self.item.title = 'Titre corrigé'
        create_portable_metadata_files(self.item, force=True)
        self.assertEqual(info.read_bytes(), original)
        create_portable_metadata_files(self.item, force=True, update=True)
        self.assertEqual(parse_portable_info(self.folder)['title'], 'Titre corrigé')
        self.assertEqual(read_folder_description(self.folder), 'Présentation du dossier')
        self.assertEqual((self.folder / 'Popinfo.txt.bak').read_bytes(), original)
        self.assertEqual((self.folder / 'cover.png').read_bytes(), b'new image')

    def test_cover_format_change_and_backup(self):
        write_source_marker(self.folder, True)
        old = self.folder / 'cover.jpg'
        old.write_bytes(b'old image')
        create_portable_metadata_files(self.item, force=True, update=True, replace_cover=True)
        self.assertFalse(old.exists())
        self.assertEqual((self.folder / 'cover.jpg.bak').read_bytes(), b'old image')
        self.assertEqual((self.folder / 'cover.png').read_bytes(), b'new image')

    def test_failed_replacement_preserves_original(self):
        target = self.folder / 'Popinfo.txt'
        target.write_bytes(b'original')
        with patch('app.utils.safe_files.os.replace', side_effect=OSError('disk error')):
            with self.assertRaises(OSError):
                atomic_write(target, b'new')
        self.assertEqual(target.read_bytes(), b'original')
        self.assertFalse(list(self.folder.glob('*.tmp')))

    def test_different_movie_sheet_is_preserved(self):
        write_source_marker(self.folder, True)
        info = self.folder / 'Popinfo.txt'
        info.write_text('file: other.mkv\ntitle: Other\n')
        create_portable_metadata_files(self.item, force=True, update=True)
        self.assertEqual(parse_portable_info(self.folder)['title'], 'Other')
