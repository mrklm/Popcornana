from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.models.media import MediaItem
from app.utils.paths import DATABASE_PATH


class MediaRepository:
    def __init__(self, db_path: Path = DATABASE_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS media (
                    id INTEGER PRIMARY KEY,
                    filepath TEXT UNIQUE,
                    media_type TEXT,
                    title TEXT,
                    original_title TEXT,
                    year INTEGER,
                    overview TEXT,
                    genres TEXT,
                    vote_average REAL,
                    poster_path TEXT,
                    backdrop_path TEXT,
                    tmdb_id INTEGER,
                    season INTEGER,
                    episode INTEGER,
                    metadata_locked INTEGER DEFAULT 0,
                    added_at TEXT
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(media)").fetchall()
            }
            if "metadata_locked" not in columns:
                connection.execute("ALTER TABLE media ADD COLUMN metadata_locked INTEGER DEFAULT 0")

    def get_setting(self, key: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return str(row["value"]) if row else None

    def set_setting(self, key: str, value: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def upsert_media(self, item: MediaItem) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO media (
                    filepath, media_type, title, original_title, year, overview, genres,
                    vote_average, poster_path, backdrop_path, tmdb_id, season, episode,
                    metadata_locked, added_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(filepath) DO UPDATE SET
                    media_type = CASE
                        WHEN media.metadata_locked = 1 AND excluded.metadata_locked = 0 THEN media.media_type
                        ELSE excluded.media_type
                    END,
                    title = CASE
                        WHEN media.metadata_locked = 1 AND excluded.metadata_locked = 0 THEN media.title
                        ELSE excluded.title
                    END,
                    original_title = CASE
                        WHEN media.metadata_locked = 1 AND excluded.metadata_locked = 0 THEN media.original_title
                        ELSE COALESCE(excluded.original_title, media.original_title)
                    END,
                    year = CASE
                        WHEN media.metadata_locked = 1 AND excluded.metadata_locked = 0 THEN media.year
                        ELSE COALESCE(excluded.year, media.year)
                    END,
                    overview = CASE
                        WHEN media.metadata_locked = 1 AND excluded.metadata_locked = 0 THEN media.overview
                        ELSE COALESCE(excluded.overview, media.overview)
                    END,
                    genres = CASE
                        WHEN media.metadata_locked = 1 AND excluded.metadata_locked = 0 THEN media.genres
                        ELSE COALESCE(excluded.genres, media.genres)
                    END,
                    vote_average = CASE
                        WHEN media.metadata_locked = 1 AND excluded.metadata_locked = 0 THEN media.vote_average
                        ELSE COALESCE(excluded.vote_average, media.vote_average)
                    END,
                    poster_path = CASE
                        WHEN media.metadata_locked = 1 AND excluded.metadata_locked = 0 THEN media.poster_path
                        ELSE COALESCE(excluded.poster_path, media.poster_path)
                    END,
                    backdrop_path = CASE
                        WHEN media.metadata_locked = 1 AND excluded.metadata_locked = 0 THEN media.backdrop_path
                        ELSE COALESCE(excluded.backdrop_path, media.backdrop_path)
                    END,
                    tmdb_id = CASE
                        WHEN media.metadata_locked = 1 AND excluded.metadata_locked = 0 THEN media.tmdb_id
                        ELSE COALESCE(excluded.tmdb_id, media.tmdb_id)
                    END,
                    season = CASE
                        WHEN media.metadata_locked = 1 AND excluded.metadata_locked = 0 THEN media.season
                        ELSE excluded.season
                    END,
                    episode = CASE
                        WHEN media.metadata_locked = 1 AND excluded.metadata_locked = 0 THEN media.episode
                        ELSE excluded.episode
                    END,
                    metadata_locked = CASE
                        WHEN excluded.metadata_locked = 1 THEN 1
                        ELSE media.metadata_locked
                    END
                """,
                (
                    str(item.filepath),
                    item.media_type,
                    item.title,
                    item.original_title,
                    item.year,
                    item.overview,
                    item.genres,
                    item.vote_average,
                    item.poster_path,
                    item.backdrop_path,
                    item.tmdb_id,
                    item.season,
                    item.episode,
                    1 if item.metadata_locked else 0,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def list_media(self) -> list[MediaItem]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM media
                ORDER BY title COLLATE NOCASE, year, season, episode
                """
            ).fetchall()
        return [self._row_to_media(row) for row in rows]

    def delete_missing_media(self) -> int:
        items = self.list_media()
        missing_paths = [str(item.filepath) for item in items if not item.filepath.exists()]
        if not missing_paths:
            return 0

        with self._connect() as connection:
            connection.executemany("DELETE FROM media WHERE filepath = ?", [(path,) for path in missing_paths])
        return len(missing_paths)

    @staticmethod
    def _row_to_media(row: sqlite3.Row) -> MediaItem:
        return MediaItem(
            filepath=Path(row["filepath"]),
            media_type=row["media_type"],
            title=row["title"],
            original_title=row["original_title"],
            year=row["year"],
            overview=row["overview"],
            genres=row["genres"],
            vote_average=row["vote_average"],
            poster_path=row["poster_path"],
            backdrop_path=row["backdrop_path"],
            tmdb_id=row["tmdb_id"],
            season=row["season"],
            episode=row["episode"],
            metadata_locked=bool(row["metadata_locked"]),
        )
