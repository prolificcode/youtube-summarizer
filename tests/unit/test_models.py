"""Unit tests for Pydantic data models.

Tests validation rules, field constraints, and helper methods for:
- VideoMetadata
- TranscriptSegment
- Transcript
- Summary
- VideoRecord
"""

import pytest
from datetime import datetime
from pydantic import ValidationError, HttpUrl
from youtube_summarizer.core.models import (
    VideoMetadata,
    TranscriptSegment,
    Transcript,
    Summary,
    VideoRecord
)


class TestVideoMetadata:
    """Test VideoMetadata model validation and methods."""

    def test_valid_video_metadata(self):
        """Test creation with valid data."""
        metadata = VideoMetadata(
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            url="https://youtube.com/watch?v=dQw4w9WgXcQ",
            duration_seconds=180
        )
        assert metadata.video_id == "dQw4w9WgXcQ"
        assert metadata.title == "Test Video"
        assert metadata.duration_seconds == 180

    def test_video_metadata_with_optional_fields(self):
        """Test creation with all optional fields."""
        metadata = VideoMetadata(
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            channel_name="Test Channel",
            publish_date="2024-01-15",
            url="https://youtube.com/watch?v=dQw4w9WgXcQ",
            duration_seconds=300
        )
        assert metadata.channel_name == "Test Channel"
        assert metadata.publish_date == "2024-01-15"

    def test_video_id_validation_too_short(self):
        """Test video_id must be exactly 11 characters."""
        with pytest.raises(ValidationError) as exc_info:
            VideoMetadata(
                video_id="short",
                title="Test",
                url="https://youtube.com/watch?v=short"
            )
        assert "video_id" in str(exc_info.value)

    def test_video_id_validation_too_long(self):
        """Test video_id cannot exceed 11 characters."""
        with pytest.raises(ValidationError) as exc_info:
            VideoMetadata(
                video_id="toolongvideoid",
                title="Test",
                url="https://youtube.com/watch?v=toolong"
            )
        assert "video_id" in str(exc_info.value)

    def test_title_validation_empty(self):
        """Test title cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            VideoMetadata(
                video_id="dQw4w9WgXcQ",
                title="",
                url="https://youtube.com/watch?v=dQw4w9WgXcQ"
            )
        assert "title" in str(exc_info.value)

    def test_title_validation_too_long(self):
        """Test title cannot exceed 500 characters."""
        with pytest.raises(ValidationError) as exc_info:
            VideoMetadata(
                video_id="dQw4w9WgXcQ",
                title="A" * 501,
                url="https://youtube.com/watch?v=dQw4w9WgXcQ"
            )
        assert "title" in str(exc_info.value)

    def test_duration_validation_negative(self):
        """Test duration cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            VideoMetadata(
                video_id="dQw4w9WgXcQ",
                title="Test",
                url="https://youtube.com/watch?v=test",
                duration_seconds=-1
            )
        assert "duration_seconds" in str(exc_info.value)

    def test_duration_formatted_short_video(self):
        """Test duration formatting for videos under 1 hour."""
        metadata = VideoMetadata(
            video_id="dQw4w9WgXcQ",
            title="Test",
            url="https://youtube.com/watch?v=test",
            duration_seconds=90
        )
        assert metadata.duration_formatted == "1:30"

    def test_duration_formatted_long_video(self):
        """Test duration formatting for videos over 1 hour."""
        metadata = VideoMetadata(
            video_id="dQw4w9WgXcQ",
            title="Test",
            url="https://youtube.com/watch?v=test",
            duration_seconds=3661
        )
        assert metadata.duration_formatted == "1:01:01"

    def test_duration_formatted_exact_hour(self):
        """Test duration formatting for exactly 1 hour."""
        metadata = VideoMetadata(
            video_id="dQw4w9WgXcQ",
            title="Test",
            url="https://youtube.com/watch?v=test",
            duration_seconds=3600
        )
        assert metadata.duration_formatted == "1:00:00"

    def test_duration_formatted_none(self):
        """Test duration formatting when duration is None."""
        metadata = VideoMetadata(
            video_id="dQw4w9WgXcQ",
            title="Test",
            url="https://youtube.com/watch?v=test"
        )
        assert metadata.duration_formatted == "Unknown"


class TestTranscriptSegment:
    """Test TranscriptSegment model."""

    def test_valid_segment(self):
        """Test creation with valid data."""
        segment = TranscriptSegment(
            text="Hello world",
            start=0.0,
            duration=2.5
        )
        assert segment.text == "Hello world"
        assert segment.start == 0.0
        assert segment.duration == 2.5

    def test_segment_without_duration(self):
        """Test creation without duration (optional field)."""
        segment = TranscriptSegment(
            text="Hello world",
            start=0.0
        )
        assert segment.text == "Hello world"
        assert segment.start == 0.0
        assert segment.duration is None


class TestTranscript:
    """Test Transcript model and methods."""

    def test_valid_transcript(self):
        """Test creation with valid data."""
        transcript = Transcript(
            video_id="dQw4w9WgXcQ",
            segments=[
                TranscriptSegment(text="Hello", start=0.0, duration=1.0),
                TranscriptSegment(text="World", start=1.0, duration=1.0)
            ],
            language="en",
            is_auto_generated=False
        )
        assert transcript.video_id == "dQw4w9WgXcQ"
        assert len(transcript.segments) == 2
        assert transcript.language == "en"
        assert not transcript.is_auto_generated

    def test_transcript_default_language(self):
        """Test default language is 'en'."""
        transcript = Transcript(
            video_id="dQw4w9WgXcQ",
            segments=[]
        )
        assert transcript.language == "en"

    def test_transcript_default_auto_generated(self):
        """Test default is_auto_generated is False."""
        transcript = Transcript(
            video_id="dQw4w9WgXcQ",
            segments=[]
        )
        assert transcript.is_auto_generated is False

    def test_full_text_property(self):
        """Test full_text concatenates all segments."""
        transcript = Transcript(
            video_id="dQw4w9WgXcQ",
            segments=[
                TranscriptSegment(text="Hello", start=0.0, duration=1.0),
                TranscriptSegment(text="beautiful", start=1.0, duration=1.0),
                TranscriptSegment(text="world", start=2.0, duration=1.0)
            ]
        )
        assert transcript.full_text == "Hello beautiful world"

    def test_full_text_empty_segments(self):
        """Test full_text with no segments."""
        transcript = Transcript(
            video_id="dQw4w9WgXcQ",
            segments=[]
        )
        assert transcript.full_text == ""

    def test_get_text_at_time(self):
        """Test extracting text for a specific time range."""
        transcript = Transcript(
            video_id="dQw4w9WgXcQ",
            segments=[
                TranscriptSegment(text="First", start=0.0, duration=5.0),
                TranscriptSegment(text="Second", start=5.0, duration=5.0),
                TranscriptSegment(text="Third", start=10.0, duration=5.0),
                TranscriptSegment(text="Fourth", start=15.0, duration=5.0)
            ]
        )
        # Get segments between 5 and 15 seconds
        result = transcript.get_text_at_time(5.0, 15.0)
        assert "Second" in result
        assert "Third" in result
        assert "First" not in result
        assert "Fourth" not in result

    def test_get_text_at_time_no_matches(self):
        """Test get_text_at_time with no matching segments."""
        transcript = Transcript(
            video_id="dQw4w9WgXcQ",
            segments=[
                TranscriptSegment(text="First", start=0.0, duration=5.0),
                TranscriptSegment(text="Second", start=5.0, duration=5.0)
            ]
        )
        # Request time range with no segments
        result = transcript.get_text_at_time(100.0, 200.0)
        assert result == ""


class TestSummary:
    """Test Summary model validation."""

    def test_valid_summary(self):
        """Test creation with valid data."""
        summary = Summary(
            video_id=1,
            summary_text="This is a valid summary with enough content.",
            model_name="llama3.1:8b"
        )
        assert summary.video_id == 1
        assert summary.summary_text == "This is a valid summary with enough content."
        assert summary.model_name == "llama3.1:8b"

    def test_summary_with_all_fields(self):
        """Test creation with all optional fields."""
        now = datetime.now()
        summary = Summary(
            id=1,
            video_id=2,
            summary_text="Complete summary with all metadata fields populated.",
            model_name="llama3.1:8b",
            prompt_version="v2",
            token_count=150,
            generation_time_seconds=5.2,
            created_at=now
        )
        assert summary.id == 1
        assert summary.prompt_version == "v2"
        assert summary.token_count == 150
        assert summary.generation_time_seconds == 5.2
        assert summary.created_at == now

    def test_summary_text_too_short(self):
        """Test summary_text must be at least 10 characters."""
        with pytest.raises(ValidationError) as exc_info:
            Summary(
                video_id=1,
                summary_text="Short",
                model_name="llama3.1:8b"
            )
        assert "summary_text" in str(exc_info.value)

    def test_summary_default_prompt_version(self):
        """Test default prompt_version is 'v1'."""
        summary = Summary(
            video_id=1,
            summary_text="This is a valid summary with enough content.",
            model_name="llama3.1:8b"
        )
        assert summary.prompt_version == "v1"


class TestVideoRecord:
    """Test VideoRecord model."""

    def test_valid_video_record(self):
        """Test creation with valid data."""
        record = VideoRecord(
            id=1,
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            url="https://youtube.com/watch?v=dQw4w9WgXcQ",
            duration_seconds=180
        )
        assert record.id == 1
        assert record.video_id == "dQw4w9WgXcQ"
        assert record.title == "Test Video"

    def test_video_record_with_summaries(self):
        """Test video record with associated summaries."""
        summaries = [
            Summary(
                video_id=1,
                summary_text="First summary with sufficient length.",
                model_name="llama3.1:8b"
            ),
            Summary(
                video_id=1,
                summary_text="Second summary also with sufficient length.",
                model_name="qwen2.5:7b"
            )
        ]

        record = VideoRecord(
            id=1,
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            url="https://youtube.com/watch?v=dQw4w9WgXcQ",
            summaries=summaries
        )
        assert len(record.summaries) == 2
        assert record.summaries[0].model_name == "llama3.1:8b"
        assert record.summaries[1].model_name == "qwen2.5:7b"

    def test_video_record_default_summaries(self):
        """Test default summaries is empty list."""
        record = VideoRecord(
            id=1,
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            url="https://youtube.com/watch?v=test"
        )
        assert record.summaries == []
        assert isinstance(record.summaries, list)
