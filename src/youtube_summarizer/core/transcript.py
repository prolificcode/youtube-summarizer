"""YouTube transcript fetching service.

This module provides functionality to fetch and process YouTube video transcripts
using the youtube-transcript-api library. It handles multiple transcript formats,
language preferences, and graceful fallbacks.
"""

import re
from typing import Optional

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

from youtube_summarizer.core.models import Transcript, TranscriptSegment
from youtube_summarizer.core.exceptions import (
    TranscriptNotAvailableError,
    TranscriptError,
    InvalidVideoURLError,
)


class TranscriptService:
    """Service for fetching YouTube video transcripts.

    This service provides methods to extract video IDs from YouTube URLs,
    fetch transcripts with language preferences, and handle various
    transcript availability scenarios.

    Attributes:
        preferred_languages: List of language codes in order of preference

    Example:
        >>> service = TranscriptService(preferred_languages=['en', 'es'])
        >>> video_id = service.extract_video_id('https://youtube.com/watch?v=abc123')
        >>> transcript = service.fetch_transcript(video_id)
        >>> print(transcript.full_text)
    """

    def __init__(self, preferred_languages: Optional[list[str]] = None):
        """Initialize the transcript service.

        Args:
            preferred_languages: Language preference order (default: ['en'])
                Language codes should be in ISO 639-1 format (e.g., 'en', 'es', 'fr')
        """
        self.preferred_languages = preferred_languages or ['en']

    def extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL or validate direct video ID.

        Supports multiple YouTube URL formats:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/v/VIDEO_ID
        - Direct video ID (11 characters)

        Args:
            url: YouTube URL or video ID string

        Returns:
            11-character YouTube video ID

        Raises:
            InvalidVideoURLError: If URL is invalid or video ID cannot be extracted

        Example:
            >>> service = TranscriptService()
            >>> service.extract_video_id('https://youtube.com/watch?v=dQw4w9WgXcQ')
            'dQw4w9WgXcQ'
            >>> service.extract_video_id('dQw4w9WgXcQ')
            'dQw4w9WgXcQ'
        """
        # YouTube video ID patterns
        patterns = [
            r'(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})',
            r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'(?:youtube\.com/v/)([a-zA-Z0-9_-]{11})',
            r'^([a-zA-Z0-9_-]{11})$'  # Direct video ID
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        raise InvalidVideoURLError(
            f"Invalid YouTube URL or video ID: '{url}'. "
            "Expected a valid YouTube URL or 11-character video ID."
        )

    def fetch_transcript(
        self,
        video_id: str,
        language: Optional[str] = None
    ) -> Transcript:
        """Fetch transcript for a YouTube video.

        Implements a fallback strategy for transcript fetching:
        1. Try manually created transcript in preferred language
        2. Fallback to auto-generated transcript
        3. Try other available languages if specified language unavailable

        Args:
            video_id: YouTube video ID (11 characters)
            language: Specific language code (overrides preferred_languages)
                If None, uses the first language from preferred_languages

        Returns:
            Transcript object containing all segments and metadata

        Raises:
            TranscriptNotAvailableError: No transcript available for this video
            TranscriptError: API error or other failure during fetching

        Example:
            >>> service = TranscriptService()
            >>> transcript = service.fetch_transcript('dQw4w9WgXcQ')
            >>> print(f"Language: {transcript.language}")
            >>> print(f"Segments: {len(transcript.segments)}")
            >>> print(f"Auto-generated: {transcript.is_auto_generated}")
        """
        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)

            # Determine target language
            target_lang = language or self.preferred_languages[0]

            # Try manual transcript first
            is_auto_generated = False
            transcript_data = None

            try:
                transcript_data = transcript_list.find_manually_created_transcript(
                    [target_lang]
                )
            except NoTranscriptFound:
                # Fallback to auto-generated
                try:
                    transcript_data = transcript_list.find_generated_transcript(
                        [target_lang]
                    )
                    is_auto_generated = True
                except NoTranscriptFound:
                    # If specific language not found, try any available transcript
                    if not language:
                        # Try other preferred languages
                        for lang in self.preferred_languages[1:]:
                            try:
                                transcript_data = transcript_list.find_manually_created_transcript(
                                    [lang]
                                )
                                break
                            except NoTranscriptFound:
                                try:
                                    transcript_data = transcript_list.find_generated_transcript(
                                        [lang]
                                    )
                                    is_auto_generated = True
                                    break
                                except NoTranscriptFound:
                                    continue

                    if transcript_data is None:
                        raise TranscriptNotAvailableError(
                            f"No transcript available for video {video_id} "
                            f"in language '{target_lang}'"
                        )

            # Fetch actual transcript data
            segments_raw = transcript_data.fetch()
            segments = [
                TranscriptSegment(
                    text=seg.text,
                    start=seg.start,
                    duration=seg.duration
                )
                for seg in segments_raw
            ]

            return Transcript(
                video_id=video_id,
                segments=segments,
                language=transcript_data.language_code,
                is_auto_generated=is_auto_generated
            )

        except TranscriptsDisabled:
            raise TranscriptNotAvailableError(
                f"Transcripts are disabled for video {video_id}"
            )
        except VideoUnavailable:
            raise TranscriptNotAvailableError(
                f"Video {video_id} is unavailable (may be private or deleted)"
            )
        except TranscriptNotAvailableError:
            raise
        except Exception as e:
            raise TranscriptError(
                f"Failed to fetch transcript for video {video_id}: {str(e)}"
            )

    def get_available_languages(self, video_id: str) -> list[str]:
        """Get list of available transcript languages for a video.

        Args:
            video_id: YouTube video ID (11 characters)

        Returns:
            List of ISO 639-1 language codes (e.g., ['en', 'es', 'fr'])
            Returns empty list if video has no transcripts or on error

        Example:
            >>> service = TranscriptService()
            >>> languages = service.get_available_languages('dQw4w9WgXcQ')
            >>> print(f"Available languages: {', '.join(languages)}")
        """
        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            return [t.language_code for t in transcript_list]
        except Exception:
            return []
