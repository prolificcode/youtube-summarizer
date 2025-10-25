"""Core data models for YouTube Summarizer.

This module defines all Pydantic data models used throughout the application,
providing type-safe data structures with automatic validation for video metadata,
transcripts, summaries, and database records.
"""

from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from datetime import datetime
from typing import Optional


class VideoMetadata(BaseModel):
    """YouTube video metadata with validation.

    This model represents the core metadata for a YouTube video,
    including identifiers, descriptive information, and duration.

    Attributes:
        video_id: Unique 11-character YouTube video identifier
        title: Video title (1-500 characters)
        channel_name: Name of the channel that published the video
        publish_date: Video publication date in ISO format (YYYY-MM-DD)
        url: Full YouTube video URL
        duration_seconds: Video duration in seconds (non-negative)
    """
    video_id: str = Field(..., min_length=11, max_length=11, description="YouTube video ID")
    title: str = Field(..., min_length=1, max_length=500, description="Video title")
    channel_name: Optional[str] = Field(None, description="Channel name")
    publish_date: Optional[str] = Field(None, description="Publication date (ISO format YYYY-MM-DD)")
    url: HttpUrl = Field(..., description="Full YouTube video URL")
    duration_seconds: Optional[int] = Field(None, ge=0, description="Video duration in seconds")

    @property
    def duration_formatted(self) -> str:
        """Return duration as HH:MM:SS or MM:SS format.

        Returns:
            Formatted duration string. If duration is unknown, returns "Unknown".
            For videos over 1 hour: "H:MM:SS"
            For videos under 1 hour: "M:SS"

        Examples:
            - 90 seconds -> "1:30"
            - 3661 seconds -> "1:01:01"
            - None -> "Unknown"
        """
        if not self.duration_seconds:
            return "Unknown"
        hours, remainder = divmod(self.duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


class TranscriptSegment(BaseModel):
    """Individual transcript segment with timestamp information.

    Represents a single timestamped segment of a video transcript,
    typically corresponding to a caption or subtitle entry.

    Attributes:
        text: The transcript text for this segment
        start: Start time of the segment in seconds
        duration: Duration of the segment in seconds (optional)
    """
    text: str = Field(..., description="Transcript text segment")
    start: float = Field(..., description="Start time in seconds")
    duration: Optional[float] = Field(None, description="Duration in seconds")


class Transcript(BaseModel):
    """Complete video transcript with all segments.

    Represents the full transcript of a video, including all timestamped
    segments and metadata about the transcript itself.

    Attributes:
        video_id: YouTube video ID this transcript belongs to
        segments: List of timestamped transcript segments
        language: Language code of the transcript (e.g., 'en', 'es')
        is_auto_generated: Whether the transcript was auto-generated
    """
    video_id: str = Field(..., description="YouTube video ID")
    segments: list[TranscriptSegment] = Field(..., description="List of transcript segments")
    language: str = Field(default="en", description="Transcript language code")
    is_auto_generated: bool = Field(default=False, description="Whether transcript is auto-generated")

    @property
    def full_text(self) -> str:
        """Concatenate all segments into a single transcript text.

        Returns:
            Complete transcript as a single string with segments
            separated by spaces.

        Example:
            If segments contain ["Hello", "world", "today"], returns "Hello world today"
        """
        return ' '.join(seg.text for seg in self.segments)

    def get_text_at_time(self, start_time: float, end_time: float) -> str:
        """Extract transcript text for a specific time range.

        Args:
            start_time: Beginning of time range in seconds
            end_time: End of time range in seconds

        Returns:
            Concatenated text from all segments within the time range,
            separated by spaces. Returns empty string if no segments
            fall within the specified range.

        Example:
            transcript.get_text_at_time(10.0, 30.0)
            # Returns all transcript text between 10 and 30 seconds
        """
        relevant = [seg.text for seg in self.segments
                   if start_time <= seg.start <= end_time]
        return ' '.join(relevant)


class Summary(BaseModel):
    """Video summary with generation metadata.

    Represents a generated summary for a video, including the summary
    text itself and metadata about how and when it was generated.

    Attributes:
        id: Database ID (None before saving to database)
        video_id: Foreign key reference to the videos table
        summary_text: The generated summary text (minimum 10 characters)
        model_name: Name of the LLM model used (e.g., "llama3.1:8b")
        prompt_version: Version of the prompt template used
        token_count: Number of tokens in the generated summary
        generation_time_seconds: Time taken to generate the summary
        created_at: Timestamp when the summary was created
    """
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

    id: Optional[int] = Field(None, description="Database ID (None before saving)")
    video_id: int = Field(..., description="Foreign key to videos table")
    summary_text: str = Field(..., min_length=10, description="Generated summary text")
    model_name: str = Field(..., description="LLM model name used for generation")
    prompt_version: str = Field(default="v1", description="Prompt template version")
    token_count: Optional[int] = Field(None, description="Number of tokens in summary")
    generation_time_seconds: Optional[float] = Field(None, description="Generation time in seconds")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")


class VideoRecord(BaseModel):
    """Complete video record from database with associated summaries.

    Represents a complete video record as stored in the database,
    including all metadata and associated summaries.

    This model is used when retrieving video records from the database
    and includes the database ID and creation timestamp along with
    all video metadata and related summaries.

    Attributes:
        id: Database primary key
        video_id: YouTube video ID (11 characters)
        title: Video title
        channel_name: Channel name
        publish_date: Publication date in ISO format
        url: Full YouTube video URL
        duration_seconds: Video duration in seconds
        created_at: When the record was first saved
        summaries: List of all summaries generated for this video
    """
    id: Optional[int] = Field(None, description="Database primary key")
    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    channel_name: Optional[str] = Field(None, description="Channel name")
    publish_date: Optional[str] = Field(None, description="Publication date (ISO format)")
    url: str = Field(..., description="Full YouTube video URL")
    duration_seconds: Optional[int] = Field(None, description="Video duration in seconds")
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")
    summaries: list[Summary] = Field(default_factory=list, description="Associated summaries")
