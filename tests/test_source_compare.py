import tempfile
import unittest
from pathlib import Path

from app.database.repository import MediaRepository
from app.models.media import MediaItem
from app.utils.source_compare import (
    Choice, apply_operations, build_operations, check_conflicts, collect_pair, collect_side, database_renames,
    find_pairs, pair_is_identical, row_keys, undo_operations, validate_name,
)

FOLDER = "film super - realisateur truc - 2008"


class SourceCompareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name).resolve()
        self.left_root, self.right_root = base / "interne", base / "externe"
        left, right = self.left_root / FOLDER, self.right_root / FOLDER
        left.mkdir(parents=True)
        right.mkdir(parents=True)
        (left / f"{FOLDER}.mkv").write_bytes(b"v" * 1000)
        (right / "film super 2008 YTF torrent 1080p par kikou50.mkv").write_bytes(b"v" * 1000)
        (left / "film super.srt").write_text("gauche")
        (right / f"{FOLDER}.srt").write_text("droite, meilleur")
        (left / "cover.jpg").write_bytes(b"petite")
        (right / "cover.jpg").write_bytes(b"grande et nette")
        (left / "Popinfo.txt").write_text("title: Film super\nfile: autre.mkv\n\nsynopsis:\nfile: reste\n")
        # Une autre vidéo sans équivalent et une série, ignorées.
        (self.left_root / "seul").mkdir()
        (self.left_root / "seul" / "seul.mkv").write_bytes(b"x" * 5)
        (self.right_root / "serie").mkdir()
        (self.right_root / "serie" / "Serie S01E01.mkv").write_bytes(b"x" * 5)

    def sides(self):
        pairs, ambiguous = find_pairs(self.left_root, self.right_root)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(ambiguous, 0)
        left_video, right_video = pairs[0]
        return {"left": collect_side(self.left_root, left_video), "right": collect_side(self.right_root, right_video)}

    def test_user_example(self):
        sides = self.sides()
        self.assertFalse(pair_is_identical(sides["left"], sides["right"]))
        self.assertEqual(row_keys(sides["left"], sides["right"]), ["video", "folder", "sub:", "cover"])
        choices = {
            "video": Choice("left", FOLDER),
            "sub:": Choice("right", FOLDER),
            "cover": Choice("right", "cover"),
        }
        operations = build_operations(sides, choices)
        self.assertEqual(check_conflicts(operations), [])
        done, error = apply_operations(operations)
        self.assertIsNone(error)
        left, right = self.left_root / FOLDER, self.right_root / FOLDER
        self.assertTrue((right / f"{FOLDER}.mkv").exists())
        self.assertFalse((right / "film super 2008 YTF torrent 1080p par kikou50.mkv").exists())
        self.assertEqual((left / f"{FOLDER}.srt").read_text(), "droite, meilleur")
        self.assertEqual((left / "film super.srt.bak").read_text(), "gauche")
        self.assertEqual((left / "cover.jpg").read_bytes(), b"grande et nette")
        self.assertEqual((left / "cover.jpg.bak").read_bytes(), b"petite")
        # Popinfo : « file: » suit la vidéo, le synopsis est intact.
        self.assertEqual((left / "Popinfo.txt").read_text(), f"title: Film super\nfile: {FOLDER}.mkv\n\nsynopsis:\nfile: reste\n")
        self.assertTrue(pair_is_identical(*self.sides().values()))

        self.assertEqual(undo_operations(done), [])
        self.assertTrue((right / "film super 2008 YTF torrent 1080p par kikou50.mkv").exists())
        self.assertEqual((left / "film super.srt").read_text(), "gauche")
        self.assertFalse((left / f"{FOLDER}.srt").exists())
        self.assertEqual((left / "cover.jpg").read_bytes(), b"petite")
        self.assertEqual(sorted(p.name for p in left.iterdir()),
                         sorted([f"{FOLDER}.mkv", "film super.srt", "cover.jpg", "Popinfo.txt"]))

    def test_edited_folder_name_and_conflict(self):
        sides = self.sides()
        operations = build_operations(sides, {"folder": Choice("left", "Film Super (2008)")})
        self.assertEqual([op["op"] for op in operations], ["rename", "rename"])
        (self.right_root / "Film Super (2008)").mkdir()
        self.assertEqual(check_conflicts(operations), [str(self.right_root / "Film Super (2008)")])

    def test_ambiguous_sizes_skipped(self):
        (self.right_root / "copie").mkdir()
        (self.right_root / "copie" / "copie.mkv").write_bytes(b"v" * 1000)
        pairs, ambiguous = find_pairs(self.left_root, self.right_root)
        self.assertEqual((pairs, ambiguous), ([], 1))

    def test_single_subtitles_face_to_face(self):
        right = self.right_root / FOLDER
        (right / f"{FOLDER}.srt").rename(right / f"{FOLDER}.fr.srt")
        pairs, _ = find_pairs(self.left_root, self.right_root)
        sides = collect_pair(self.left_root, pairs[0][0], self.right_root, pairs[0][1])
        self.assertEqual(row_keys(sides["left"], sides["right"]), ["video", "folder", "sub:fr", "cover"])
        operations = build_operations(sides, {"sub:fr": Choice("right", f"{FOLDER}.fr")})
        self.assertEqual([op["op"] for op in operations], ["aside", "copy"])
        self.assertTrue(operations[0]["src"].endswith("film super.srt"))

    def test_validate_name(self):
        self.assertIsNone(validate_name("Film - Réalisateur - 2008"))
        for name in ("", " film", "film.", "a/b", "a:b", ".cache"):
            self.assertIsNotNone(validate_name(name), name)

    def test_database_follows_renames(self):
        repository = MediaRepository(Path(self.temp.name) / "media.db")
        folder = self.right_root / FOLDER
        video = folder / "film super 2008 YTF torrent 1080p par kikou50.mkv"
        repository.upsert_media(MediaItem(filepath=video, media_type="movie", title="Film super",
                                          poster_path=str(folder / "cover.jpg"), metadata_locked=True))
        repository.set_folder_category(str(folder), "movie")
        repository.set_setting("folder_description:" + str(folder), "description")
        new_folder = self.right_root / "Film Super (2008)"
        operations = [
            {"op": "rename", "src": str(video), "dst": str(folder / f"{FOLDER}.mkv")},
            {"op": "aside", "src": str(folder / "cover.jpg"), "dst": str(folder / "cover.jpg.bak")},
            {"op": "copy", "src": "x", "dst": str(folder / "cover.png")},
            {"op": "rename", "src": str(folder), "dst": str(new_folder)},
        ]
        for old, new in database_renames(operations):
            repository.rename_path(old, new)
        item = repository.list_media()[0]
        self.assertEqual(item.filepath, new_folder / f"{FOLDER}.mkv")
        self.assertEqual(item.poster_path, str(new_folder / "cover.png"))
        self.assertTrue(item.metadata_locked)
        self.assertEqual(repository.list_folder_categories(), {str(new_folder): "movie"})
        self.assertEqual(repository.get_setting("folder_description:" + str(new_folder)), "description")


if __name__ == "__main__":
    unittest.main()
