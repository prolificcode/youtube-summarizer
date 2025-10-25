"""Shared pytest fixtures and configuration for all tests.

This module provides reusable fixtures for testing, including:
- Temporary directories and files
- In-memory database instances
- Mock Ollama clients
- Sample test data (video metadata, transcripts)
- Test configuration settings
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from youtube_summarizer.core.storage import StorageService
from youtube_summarizer.config import Settings
from youtube_summarizer.core.models import VideoMetadata, Transcript, TranscriptSegment


@pytest.fixture
def temp_dir():
    """Temporary directory for test files.

    Creates a temporary directory that is automatically cleaned up
    after the test completes.

    Yields:
        Path: Path object pointing to the temporary directory

    Example:
        def test_file_creation(temp_dir):
            test_file = temp_dir / "test.txt"
            test_file.write_text("Hello")
            assert test_file.exists()
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def in_memory_db():
    """In-memory SQLite database for testing.

    Creates an in-memory database instance that is automatically
    initialized and cleaned up after the test completes.

    Yields:
        StorageService: Initialized storage service with in-memory database

    Example:
        def test_storage(in_memory_db):
            video_id = in_memory_db.save_video(metadata)
            assert video_id > 0
    """
    storage = StorageService(":memory:")
    storage.connect()
    storage.initialize()
    yield storage
    storage.close()


@pytest.fixture
def test_settings(temp_dir):
    """Test configuration with temporary paths.

    Creates a Settings instance configured to use temporary directories
    for database and log files.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Settings: Configured settings instance for testing

    Example:
        def test_config(test_settings):
            assert test_settings.ollama_host == "http://localhost:11434"
    """
    return Settings(
        database_path=str(temp_dir / "test.db"),
        ollama_host="http://localhost:11434",
        default_model="llama3.1:8b",
        log_file=str(temp_dir / "test.log"),
        log_level="DEBUG"
    )


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for unit tests.

    Creates a MagicMock instance configured to simulate Ollama API responses
    without requiring an actual Ollama service.

    Returns:
        MagicMock: Mocked Ollama client with pre-configured responses

    Example:
        def test_summarization(mock_ollama_client):
            service = SummarizerService(settings)
            service.client = mock_ollama_client
            summary = service.summarize(transcript, metadata)
            assert summary.summary_text == "This is a mock summary of the video content."
    """
    client = MagicMock()

    # Mock list() method to return available models
    client.list.return_value = {
        'models': [
            {'name': 'llama3.1:8b', 'size': 4700000000},
            {'name': 'qwen2.5:7b', 'size': 4200000000}
        ]
    }

    # Mock generate() method to return a summary
    client.generate.return_value = {
        'response': 'This is a mock summary of the video content.'
    }

    # Mock chat() method as alternative
    client.chat.return_value = {
        'message': {
            'content': 'This is a mock summary of the video content.'
        }
    }

    return client


@pytest.fixture
def sample_video_metadata():
    """Sample video metadata for testing.

    Creates a VideoMetadata instance with realistic test data
    that can be used across multiple tests.

    Returns:
        VideoMetadata: Sample video metadata

    Example:
        def test_video_save(in_memory_db, sample_video_metadata):
            video_id = in_memory_db.save_video(sample_video_metadata)
            assert video_id > 0
    """
    return VideoMetadata(
        video_id="dQw4w9WgXcQ",
        title="Sample Video Title - Testing YouTube Summarizer",
        channel_name="Test Channel",
        publish_date="2024-01-01",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        duration_seconds=210
    )


@pytest.fixture
def sample_transcript():
    """Sample transcript for testing.

    Creates a Transcript instance with multiple segments that can be used
    to test transcript processing and summarization.

    Returns:
        Transcript: Sample transcript with multiple segments

    Example:
        def test_full_text(sample_transcript):
            assert "Welcome to this video" in sample_transcript.full_text
    """
    return Transcript(
        video_id="dQw4w9WgXcQ",
        segments=[
            TranscriptSegment(text="Welcome to this video", start=0.0, duration=2.0),
            TranscriptSegment(text="Today we'll discuss", start=2.0, duration=2.0),
            TranscriptSegment(text="machine learning basics", start=4.0, duration=2.0),
            TranscriptSegment(text="including neural networks", start=6.0, duration=2.0),
            TranscriptSegment(text="and deep learning concepts", start=8.0, duration=2.0),
        ],
        language="en",
        is_auto_generated=False
    )


@pytest.fixture
def sample_long_transcript():
    """Sample long transcript for testing chunking.

    Creates a long transcript that exceeds typical token limits,
    useful for testing transcript chunking logic.

    Returns:
        Transcript: Long transcript with many segments
    """
    segments = []
    for i in range(100):
        segments.append(
            TranscriptSegment(
                text=f"This is segment number {i} with some content about various topics. " * 5,
                start=float(i * 10),
                duration=10.0
            )
        )

    return Transcript(
        video_id="longvideo123",
        segments=segments,
        language="en",
        is_auto_generated=True
    )


@pytest.fixture
def mock_transcript_api():
    """Mock YouTubeTranscriptApi for unit tests.

    Creates a MagicMock instance that simulates the YouTube Transcript API
    without making actual network requests.

    Returns:
        MagicMock: Mocked transcript API
    """
    mock_api = MagicMock()

    # Mock successful transcript fetch
    mock_transcript = MagicMock()
    mock_transcript.language_code = "en"
    mock_transcript.is_generated = False
    mock_transcript.fetch.return_value = [
        {'text': 'Hello', 'start': 0.0, 'duration': 1.0},
        {'text': 'World', 'start': 1.0, 'duration': 1.0}
    ]

    mock_list = MagicMock()
    mock_list.find_manually_created_transcript.return_value = mock_transcript
    mock_api.list_transcripts.return_value = mock_list

    return mock_api
