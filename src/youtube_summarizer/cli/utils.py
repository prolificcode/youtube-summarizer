"""CLI utility functions for YouTube Summarizer.

This module provides utility functions for the CLI layer, including
video metadata extraction using yt-dlp and other helper functions.
"""

from typing import Optional
import yt_dlp

from youtube_summarizer.core.models import VideoMetadata
from youtube_summarizer.core.exceptions import TranscriptError


def extract_video_metadata(url: str) -> VideoMetadata:
    """Extract video metadata using yt-dlp.

    Uses yt-dlp to fetch comprehensive metadata about a YouTube video
    without downloading the video itself. This includes title, channel,
    duration, publish date, and other information.

    Args:
        url: YouTube video URL or video ID

    Returns:
        VideoMetadata object with extracted information

    Raises:
        TranscriptError: If metadata extraction fails (invalid URL, private video, etc.)

    Example:
        >>> metadata = extract_video_metadata("https://youtube.com/watch?v=dQw4w9WgXcQ")
        >>> print(f"Title: {metadata.title}")
        >>> print(f"Duration: {metadata.duration_formatted}")
    """
    # Configure yt-dlp options for metadata extraction only
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
        'no_color': True,
        'ignoreerrors': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info without downloading
            info = ydl.extract_info(url, download=False)

            if not info:
                raise TranscriptError(f"Could not extract video information from URL: {url}")

            # Extract and format publish date (from YYYYMMDD to YYYY-MM-DD)
            publish_date = None
            if info.get('upload_date'):
                upload_date_str = info['upload_date']
                if len(upload_date_str) == 8:  # YYYYMMDD format
                    publish_date = f"{upload_date_str[:4]}-{upload_date_str[4:6]}-{upload_date_str[6:]}"

            # Build full URL if not provided
            video_id = info['id']
            full_url = url if url.startswith('http') else f"https://www.youtube.com/watch?v={video_id}"

            # Create VideoMetadata object
            return VideoMetadata(
                video_id=video_id,
                title=info.get('title', 'Unknown Title'),
                channel_name=info.get('uploader') or info.get('channel', None),
                publish_date=publish_date,
                url=full_url,
                duration_seconds=info.get('duration', None)
            )

    except yt_dlp.utils.DownloadError as e:
        raise TranscriptError(f"Failed to extract video metadata: {str(e)}")
    except Exception as e:
        raise TranscriptError(f"Unexpected error extracting video metadata: {str(e)}")


def format_duration(seconds: Optional[int]) -> str:
    """Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds (can be None)

    Returns:
        Formatted duration string (e.g., "5:23", "1:23:45", "Unknown")

    Example:
        >>> format_duration(323)
        '5:23'
        >>> format_duration(3665)
        '1:01:05'
        >>> format_duration(None)
        'Unknown'
    """
    if seconds is None:
        return "Unknown"

    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length, adding suffix if truncated.

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: String to append if text is truncated (default: "...")

    Returns:
        Truncated text with suffix if needed

    Example:
        >>> truncate_text("This is a very long text", 15)
        'This is a ve...'
        >>> truncate_text("Short", 10)
        'Short'
    """
    if len(text) <= max_length:
        return text

    truncate_at = max_length - len(suffix)
    return text[:truncate_at] + suffix


def validate_video_id_format(video_id: str) -> bool:
    """Validate that a string matches YouTube video ID format.

    YouTube video IDs are exactly 11 characters long and contain
    alphanumeric characters, underscores, and hyphens.

    Args:
        video_id: String to validate

    Returns:
        True if valid video ID format, False otherwise

    Example:
        >>> validate_video_id_format("dQw4w9WgXcQ")
        True
        >>> validate_video_id_format("invalid")
        False
    """
    if len(video_id) != 11:
        return False

    # Valid characters: a-z, A-Z, 0-9, _, -
    valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    return all(c in valid_chars for c in video_id)
