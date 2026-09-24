import tempfile
import unittest
from pathlib import Path
from app.utils.cache_cleanup import unused_images, remove_unused_images


class CacheCleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cache = self.root / 'posters'
        self.cache.mkdir()

    def image(self, name):
        path = self.cache / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'image')
        return path

    def test_only_unused_images_removed(self):
        kept = [self.image('offline.jpg'), self.image('manual/folder.png'), self.image('backdrop.jpg')]
        orphan = self.image('orphan.jpg')
        other = self.cache / 'notes.txt'
        other.write_text('keep')
        references = ['offline.jpg', str(kept[1]), '/backdrop.jpg']
        preview = unused_images(self.cache, references)
        self.assertEqual(set(preview), {orphan})
        self.assertEqual(remove_unused_images(self.cache, references, preview), (1, 5, 0))
        self.assertTrue(all(path.exists() for path in kept))
        self.assertTrue(other.exists())

    def test_sources_and_symlinks_untouched(self):
        source = self.root / 'videos'
        source.mkdir()
        cover = source / 'cover.jpg'
        cover.write_bytes(b'original')
        (self.cache / 'link.jpg').symlink_to(cover)
        (self.cache / 'linked_directory').symlink_to(source, target_is_directory=True)
        self.assertEqual(unused_images(self.cache, []), {})
        self.assertEqual(cover.read_bytes(), b'original')

    def test_new_reference_or_modified_file_preserved_after_preview(self):
        used = self.image('new_reference.jpg')
        changed = self.image('changed.jpg')
        preview = unused_images(self.cache, [])
        changed.write_bytes(b'new contents')
        self.assertEqual(remove_unused_images(self.cache, ['new_reference.jpg'], preview), (0, 0, 0))
        self.assertTrue(used.exists())
        self.assertTrue(changed.exists())

    def test_symlink_cache_not_cleaned(self):
        link = self.root / 'linked_cache'
        link.symlink_to(self.cache, target_is_directory=True)
        self.image('keep.jpg')
        self.assertEqual(unused_images(link, []), {})
