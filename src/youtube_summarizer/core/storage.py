"""SQLite database operations for videos and summaries.

This module provides a storage service for persisting video metadata and summaries
to a SQLite database. It implements CRUD operations, search functionality, and
maintains proper database schema with indexes for performance.
"""

import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime

from youtube_summarizer.core.models import VideoRecord, Summary, VideoMetadata
from youtube_summarizer.core.exceptions import StorageError


class StorageService:
    """SQLite database operations for videos and summaries.

    This service manages all database interactions including schema creation,
    CRUD operations for videos and summaries, and search functionality.
    Uses SQLite with WAL mode for better concurrency and foreign key enforcement.

    Attributes:
        db_path: Path to SQLite database file
        conn: Active database connection (None if not connected)

    Example:
        >>> service = StorageService("./data/summaries.db")
        >>> service.connect()
        >>> service.initialize()
        >>> video_id = service.save_video(metadata)
        >>> service.save_summary(summary, video_id)
        >>> service.close()
    """

    def __init__(self, db_path: str):
        """Initialize the storage service.

        Args:
            db_path: Path to SQLite database file (or ":memory:" for testing)
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Establish database connection with optimizations.

        Creates the parent directory if needed and configures the connection
        for optimal performance and data integrity.

        Raises:
            StorageError: If connection fails
        """
        try:
            # Create parent directory if needed
            if self.db_path != ":memory:":
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Dict-like row access

            # Enable WAL mode for better concurrency
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA foreign_keys=ON")

        except Exception as e:
            raise StorageError(f"Failed to connect to database: {str(e)}")

    def initialize(self) -> None:
        """Create database schema if not exists.

        Creates the videos and summaries tables along with necessary indexes
        for performance. This method is idempotent and safe to call multiple times.

        Raises:
            StorageError: If schema creation fails
        """
        if not self.conn:
            self.connect()

        try:
            cursor = self.conn.cursor()

            # Videos table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    channel_name TEXT,
                    publish_date TEXT,
                    url TEXT NOT NULL,
                    duration_seconds INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Summaries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER NOT NULL,
                    summary_text TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    prompt_version TEXT DEFAULT 'v1',
                    token_count INTEGER,
                    generation_time_seconds REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
                )
            """)

            # Indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_videos_video_id
                ON videos(video_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_summaries_video_id
                ON summaries(video_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_summaries_created_at
                ON summaries(created_at DESC)
            """)

            self.conn.commit()

        except Exception as e:
            raise StorageError(f"Failed to initialize database: {str(e)}")

    def save_video(self, metadata: VideoMetadata) -> int:
        """Save video metadata, return video DB ID.

        If video already exists (by video_id), return existing ID without
        updating. This prevents duplicate entries for the same video.

        Args:
            metadata: Video metadata to save

        Returns:
            Database ID of video record (primary key)

        Raises:
            StorageError: If save operation fails

        Example:
            >>> service = StorageService("./data/summaries.db")
            >>> service.connect()
            >>> service.initialize()
            >>> db_id = service.save_video(metadata)
            >>> print(f"Video saved with ID: {db_id}")
        """
        if not self.conn:
            raise StorageError("Database connection not established")

        cursor = self.conn.cursor()

        try:
            # Check if video exists
            cursor.execute(
                "SELECT id FROM videos WHERE video_id = ?",
                (metadata.video_id,)
            )
            row = cursor.fetchone()
            if row:
                return row['id']

            # Insert new video
            cursor.execute("""
                INSERT INTO videos (video_id, title, channel_name,
                                   publish_date, url, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metadata.video_id,
                metadata.title,
                metadata.channel_name,
                metadata.publish_date,
                str(metadata.url),
                metadata.duration_seconds
            ))

            self.conn.commit()
            return cursor.lastrowid

        except Exception as e:
            self.conn.rollback()
            raise StorageError(f"Failed to save video: {str(e)}")

    def save_summary(self, summary: Summary, video_db_id: int) -> int:
        """Save summary for video.

        Args:
            summary: Summary object to save
            video_db_id: Database ID of associated video

        Returns:
            Database ID of summary record (primary key)

        Raises:
            StorageError: If save operation fails

        Example:
            >>> service = StorageService("./data/summaries.db")
            >>> service.connect()
            >>> summary_id = service.save_summary(summary, video_db_id)
        """
        if not self.conn:
            raise StorageError("Database connection not established")

        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO summaries (video_id, summary_text, model_name,
                                     prompt_version, token_count,
                                     generation_time_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                video_db_id,
                summary.summary_text,
                summary.model_name,
                summary.prompt_version,
                summary.token_count,
                summary.generation_time_seconds
            ))

            self.conn.commit()
            return cursor.lastrowid

        except Exception as e:
            self.conn.rollback()
            raise StorageError(f"Failed to save summary: {str(e)}")

    def get_video_by_id(self, video_id: str) -> Optional[VideoRecord]:
        """Get video record by YouTube video ID.

        Includes all associated summaries ordered by creation date (newest first).

        Args:
            video_id: YouTube video ID (11 characters)

        Returns:
            VideoRecord with all summaries, or None if not found

        Example:
            >>> service = StorageService("./data/summaries.db")
            >>> service.connect()
            >>> video = service.get_video_by_id("dQw4w9WgXcQ")
            >>> if video:
            ...     print(f"Title: {video.title}")
            ...     print(f"Summaries: {len(video.summaries)}")
        """
        if not self.conn:
            raise StorageError("Database connection not established")

        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT * FROM videos WHERE video_id = ?",
            (video_id,)
        )
        video_row = cursor.fetchone()

        if not video_row:
            return None

        # Fetch all summaries for this video
        cursor.execute(
            "SELECT * FROM summaries WHERE video_id = ? ORDER BY created_at DESC",
            (video_row['id'],)
        )
        summary_rows = cursor.fetchall()

        summaries = [
            Summary(
                id=row['id'],
                video_id=row['video_id'],
                summary_text=row['summary_text'],
                model_name=row['model_name'],
                prompt_version=row['prompt_version'],
                token_count=row['token_count'],
                generation_time_seconds=row['generation_time_seconds'],
                created_at=datetime.fromisoformat(row['created_at'])
            )
            for row in summary_rows
        ]

        return VideoRecord(
            id=video_row['id'],
            video_id=video_row['video_id'],
            title=video_row['title'],
            channel_name=video_row['channel_name'],
            publish_date=video_row['publish_date'],
            url=video_row['url'],
            duration_seconds=video_row['duration_seconds'],
            created_at=datetime.fromisoformat(video_row['created_at']),
            summaries=summaries
        )

    def list_videos(self, limit: int = 50, offset: int = 0) -> list[VideoRecord]:
        """List all videos with their most recent summary.

        Args:
            limit: Maximum number of records (default: 50)
            offset: Number of records to skip for pagination (default: 0)

        Returns:
            List of VideoRecord objects ordered by creation date (newest first)

        Example:
            >>> service = StorageService("./data/summaries.db")
            >>> service.connect()
            >>> videos = service.list_videos(limit=10)
            >>> for video in videos:
            ...     print(f"{video.title} - {len(video.summaries)} summaries")
        """
        if not self.conn:
            raise StorageError("Database connection not established")

        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT * FROM videos ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        video_rows = cursor.fetchall()

        videos = []
        for video_row in video_rows:
            # Get most recent summary
            cursor.execute(
                """SELECT * FROM summaries
                   WHERE video_id = ?
                   ORDER BY created_at DESC
                   LIMIT 1""",
                (video_row['id'],)
            )
            summary_row = cursor.fetchone()

            summaries = []
            if summary_row:
                summaries = [Summary(
                    id=summary_row['id'],
                    video_id=summary_row['video_id'],
                    summary_text=summary_row['summary_text'],
                    model_name=summary_row['model_name'],
                    prompt_version=summary_row['prompt_version'],
                    token_count=summary_row['token_count'],
                    generation_time_seconds=summary_row['generation_time_seconds'],
                    created_at=datetime.fromisoformat(summary_row['created_at'])
                )]

            videos.append(VideoRecord(
                id=video_row['id'],
                video_id=video_row['video_id'],
                title=video_row['title'],
                channel_name=video_row['channel_name'],
                publish_date=video_row['publish_date'],
                url=video_row['url'],
                duration_seconds=video_row['duration_seconds'],
                created_at=datetime.fromisoformat(video_row['created_at']),
                summaries=summaries
            ))

        return videos

    def search_videos(self, query: str, limit: int = 50) -> list[VideoRecord]:
        """Search videos by title, channel name, or summary text.

        Performs a case-insensitive substring search across video titles,
        channel names, and summary text.

        Args:
            query: Search query string
            limit: Maximum results (default: 50)

        Returns:
            List of matching VideoRecord objects ordered by creation date

        Example:
            >>> service = StorageService("./data/summaries.db")
            >>> service.connect()
            >>> results = service.search_videos("python tutorial")
            >>> print(f"Found {len(results)} videos")
        """
        if not self.conn:
            raise StorageError("Database connection not established")

        cursor = self.conn.cursor()

        search_pattern = f"%{query}%"

        cursor.execute("""
            SELECT DISTINCT v.*
            FROM videos v
            LEFT JOIN summaries s ON v.id = s.video_id
            WHERE v.title LIKE ?
               OR v.channel_name LIKE ?
               OR s.summary_text LIKE ?
            ORDER BY v.created_at DESC
            LIMIT ?
        """, (search_pattern, search_pattern, search_pattern, limit))

        video_rows = cursor.fetchall()

        # Build VideoRecord objects (similar to list_videos)
        videos = []
        for video_row in video_rows:
            cursor.execute(
                "SELECT * FROM summaries WHERE video_id = ? ORDER BY created_at DESC LIMIT 1",
                (video_row['id'],)
            )
            summary_row = cursor.fetchone()

            summaries = []
            if summary_row:
                summaries = [Summary(
                    id=summary_row['id'],
                    video_id=summary_row['video_id'],
                    summary_text=summary_row['summary_text'],
                    model_name=summary_row['model_name'],
                    prompt_version=summary_row['prompt_version'],
                    token_count=summary_row['token_count'],
                    generation_time_seconds=summary_row['generation_time_seconds'],
                    created_at=datetime.fromisoformat(summary_row['created_at'])
                )]

            videos.append(VideoRecord(
                id=video_row['id'],
                video_id=video_row['video_id'],
                title=video_row['title'],
                channel_name=video_row['channel_name'],
                publish_date=video_row['publish_date'],
                url=video_row['url'],
                duration_seconds=video_row['duration_seconds'],
                created_at=datetime.fromisoformat(video_row['created_at']),
                summaries=summaries
            ))

        return videos

    def get_video_by_db_id(self, db_id: int) -> Optional[VideoRecord]:
        """Get video by database ID.

        Args:
            db_id: Database primary key ID

        Returns:
            VideoRecord if found, None otherwise

        Raises:
            StorageError: If query fails
        """
        if not self.conn:
            raise StorageError("Database connection not established")

        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM videos WHERE id = ?
            """, (db_id,))

            video_row = cursor.fetchone()
            if not video_row:
                return None

            # Fetch associated summaries
            cursor.execute("""
                SELECT * FROM summaries
                WHERE video_id = ?
                ORDER BY created_at DESC
            """, (video_row['id'],))

            summary_rows = cursor.fetchall()
            summaries = [
                Summary(
                    summary_text=row['summary_text'],
                    model_name=row['model_name'],
                    prompt_version=row['prompt_version'],
                    token_count=row['token_count'],
                    generation_time_seconds=row['generation_time_seconds'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                for row in summary_rows
            ]

            return VideoRecord(
                id=video_row['id'],
                video_id=video_row['video_id'],
                title=video_row['title'],
                channel_name=video_row['channel_name'],
                publish_date=video_row['publish_date'],
                url=video_row['url'],
                duration_seconds=video_row['duration_seconds'],
                created_at=datetime.fromisoformat(video_row['created_at']),
                summaries=summaries
            )

        except Exception as e:
            raise StorageError(f"Failed to fetch video by DB ID: {str(e)}")

    def count_videos(self) -> int:
        """Count total number of videos in database.

        Returns:
            Total count of videos

        Raises:
            StorageError: If query fails
        """
        if not self.conn:
            raise StorageError("Database connection not established")

        cursor = self.conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) as count FROM videos")
            row = cursor.fetchone()
            return row['count']
        except Exception as e:
            raise StorageError(f"Failed to count videos: {str(e)}")

    def close(self) -> None:
        """Close database connection.

        Safe to call multiple times. Does nothing if connection already closed.

        Example:
            >>> service = StorageService("./data/summaries.db")
            >>> service.connect()
            >>> # ... do work ...
            >>> service.close()
        """
        if self.conn:
            self.conn.close()
            self.conn = None
