#!/usr/bin/env python3
"""Database initialization and migration script.

This script initializes the SQLite database for the YouTube Summarizer application.
It creates the necessary tables, indexes, and can handle future schema migrations.

Usage:
    python scripts/init_database.py
    python scripts/init_database.py --db-path ./custom/path/summaries.db
    python scripts/init_database.py --reset  # WARNING: Deletes all data!

The script is idempotent - safe to run multiple times.
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from youtube_summarizer.config import get_settings
from youtube_summarizer.core.storage import StorageService
from youtube_summarizer.core.exceptions import StorageError


def initialize_database(db_path: str, reset: bool = False) -> None:
    """Initialize the database schema.

    Args:
        db_path: Path to the SQLite database file
        reset: If True, delete existing database and recreate
    """
    db_file = Path(db_path)

    if reset and db_file.exists():
        print(f"Resetting database: {db_path}")
        confirm = input("This will DELETE ALL DATA. Are you sure? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return
        db_file.unlink()
        print(f"Deleted {db_path}")

    print(f"Initializing database: {db_path}")

    # Create parent directory if needed
    db_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Initialize storage service
        storage = StorageService(db_path)
        storage.connect()
        storage.initialize()
        storage.close()

        print("\nDatabase initialized successfully!")
        print(f"Location: {db_file.absolute()}")
        print("\nTables created:")
        print("  - videos (stores video metadata)")
        print("  - summaries (stores generated summaries)")
        print("\nIndexes created:")
        print("  - idx_videos_video_id")
        print("  - idx_summaries_video_id")
        print("  - idx_summaries_created_at")

    except StorageError as e:
        print(f"\nError: Failed to initialize database: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError: Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def check_database_status(db_path: str) -> None:
    """Check database status and display information.

    Args:
        db_path: Path to the SQLite database file
    """
    db_file = Path(db_path)

    if not db_file.exists():
        print(f"Database does not exist: {db_path}")
        print("Run without --status flag to initialize.")
        return

    try:
        storage = StorageService(db_path)
        storage.connect()

        # Get table info
        cursor = storage.conn.cursor()

        # Check videos table
        cursor.execute("SELECT COUNT(*) FROM videos")
        video_count = cursor.fetchone()[0]

        # Check summaries table
        cursor.execute("SELECT COUNT(*) FROM summaries")
        summary_count = cursor.fetchone()[0]

        # Get database file size
        db_size = db_file.stat().st_size

        storage.close()

        print(f"\nDatabase Status: {db_path}")
        print(f"Location: {db_file.absolute()}")
        print(f"Size: {db_size:,} bytes ({db_size / 1024:.2f} KB)")
        print(f"\nRecords:")
        print(f"  Videos: {video_count}")
        print(f"  Summaries: {summary_count}")

    except StorageError as e:
        print(f"\nError: Failed to check database: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError: Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Initialize YouTube Summarizer database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Initialize with default path from config:
    python scripts/init_database.py

  Initialize with custom path:
    python scripts/init_database.py --db-path ./data/custom.db

  Check database status:
    python scripts/init_database.py --status

  Reset database (WARNING: deletes all data):
    python scripts/init_database.py --reset

Notes:
  - The script is idempotent and safe to run multiple times
  - Default database path is read from config (YTS_DATABASE_PATH env var)
  - Use --reset with caution as it deletes all existing data
        """
    )

    parser.add_argument(
        "--db-path",
        type=str,
        help="Path to SQLite database file (default: from config)"
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (WARNING: deletes all data)"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Check database status and exit"
    )

    args = parser.parse_args()

    # Get database path
    if args.db_path:
        db_path = args.db_path
    else:
        settings = get_settings()
        db_path = str(settings.database_path_obj)

    # Execute requested action
    if args.status:
        check_database_status(db_path)
    else:
        initialize_database(db_path, reset=args.reset)


if __name__ == "__main__":
    main()
