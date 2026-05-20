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
                    added_at TEXT
                )
                """
            )

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
                    vote_average, poster_path, backdrop_path, tmdb_id, season, episode, added_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(filepath) DO UPDATE SET
                    media_type = excluded.media_type,
                    title = excluded.title,
                    original_title = COALESCE(excluded.original_title, media.original_title),
                    year = COALESCE(excluded.year, media.year),
                    overview = COALESCE(excluded.overview, media.overview),
                    genres = COALESCE(excluded.genres, media.genres),
                    vote_average = COALESCE(excluded.vote_average, media.vote_average),
                    poster_path = COALESCE(excluded.poster_path, media.poster_path),
                    backdrop_path = COALESCE(excluded.backdrop_path, media.backdrop_path),
                    tmdb_id = COALESCE(excluded.tmdb_id, media.tmdb_id),
                    season = excluded.season,
                    episode = excluded.episode
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
        )
