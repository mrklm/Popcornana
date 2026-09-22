import tempfile
import unittest
from pathlib import Path

from app.utils.folder_metadata import (
    folder_cover, read_folder_description, write_folder_cover, write_folder_description,
)


class FolderMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_edit_and_clear_preserve_film_and_multiline_synopsis(self):
        film = 'title: Film\nfile: Film.mkv\n\nsynopsis:\nRésumé du film\nfolder_description: texte du résumé\n'
        path = self.folder / 'Popinfo.txt'
        path.write_text(film, encoding='utf-8')
        for description in ['Une bio\nAvec "citations" et accents é', 'Autre description', '']:
            write_folder_description(self.folder, description)
            self.assertEqual(read_folder_description(self.folder), description)
            self.assertEqual(path.read_text(encoding='utf-8').split('\n', 1)[1], film)

    def test_description_moves_with_folder(self):
        write_folder_description(self.folder, 'Présentation\nsur deux lignes')
        moved = self.folder / 'other-computer'
        moved.mkdir()
        (self.folder / 'Popinfo.txt').rename(moved / 'Popinfo.txt')
        self.assertEqual(read_folder_description(moved), 'Présentation\nsur deux lignes')

    def test_cover_replacement_leaves_movie_cover_untouched(self):
        movie_cover = self.folder / 'cover.jpg'
        movie_cover.write_bytes(b'movie')
        first = self.folder / 'first.png'
        first.write_bytes(b'folder png')
        second = self.folder / 'second.webp'
        second.write_bytes(b'folder webp')
        write_folder_cover(self.folder, first)
        result = write_folder_cover(self.folder, second)
        self.assertEqual(folder_cover(self.folder), result)
        self.assertEqual(result.read_bytes(), b'folder webp')
        self.assertFalse((self.folder / 'repocover.png').exists())
        self.assertEqual(movie_cover.read_bytes(), b'movie')
        self.assertEqual(write_folder_cover(self.folder, result), result)

    def test_missing_metadata(self):
        self.assertEqual(read_folder_description(self.folder), '')
        self.assertIsNone(folder_cover(self.folder))


if __name__ == '__main__':
    unittest.main()
