"""Core business logic for YouTube Summarizer.

This package contains the core functionality for the YouTube Summarizer
application, including data models, exception definitions, and service
implementations for transcript fetching, summarization, and storage.

The core package is designed to be completely independent of the CLI
interface, making it suitable for use in other contexts such as web
APIs or batch processing systems.
"""

# Import all models
from youtube_summarizer.core.models import (
    VideoMetadata,
    TranscriptSegment,
    Transcript,
    Summary,
    VideoRecord,
)

# Import all exceptions
from youtube_summarizer.core.exceptions import (
    YouTubeSummarizerError,
    TranscriptError,
    TranscriptNotAvailableError,
    InvalidVideoURLError,
    OllamaError,
    ModelNotFoundError,
    SummarizationError,
    StorageError,
    ConfigurationError,
)

# Public API exports
__all__ = [
    # Models
    "VideoMetadata",
    "TranscriptSegment",
    "Transcript",
    "Summary",
    "VideoRecord",
    # Exceptions
    "YouTubeSummarizerError",
    "TranscriptError",
    "TranscriptNotAvailableError",
    "InvalidVideoURLError",
    "OllamaError",
    "ModelNotFoundError",
    "SummarizationError",
    "StorageError",
    "ConfigurationError",
]
