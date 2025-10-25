"""Custom exception hierarchy for YouTube Summarizer.

This module defines a comprehensive exception hierarchy for handling
various error conditions that may arise during video transcript fetching,
summarization, storage, and configuration operations.
"""


class YouTubeSummarizerError(Exception):
    """Base exception for all application errors.

    All custom exceptions in the YouTube Summarizer application
    inherit from this base class, allowing for easy catching of
    any application-specific errors.
    """
    pass


# Transcript-related errors
class TranscriptError(YouTubeSummarizerError):
    """Base class for transcript-related errors.

    This exception serves as a base for all errors that occur
    during the process of fetching or processing YouTube video
    transcripts.
    """
    pass


class TranscriptNotAvailableError(TranscriptError):
    """Raised when no transcript is available for a video.

    This can occur when:
    - The video has no captions/subtitles
    - Captions are disabled by the video owner
    - The video is unavailable or private
    """
    pass


class InvalidVideoURLError(TranscriptError):
    """Raised when an invalid YouTube URL or video ID is provided.

    This occurs when the provided URL doesn't match any known
    YouTube URL format, or when a video ID doesn't meet the
    required format specifications (11 characters).
    """
    pass


# Ollama/LLM errors
class OllamaError(YouTubeSummarizerError):
    """Base class for Ollama API errors.

    This exception serves as a base for all errors related to
    communication with the Ollama service or LLM model operations.
    """
    pass


class ModelNotFoundError(OllamaError):
    """Raised when the requested LLM model is not available.

    This occurs when:
    - The specified model hasn't been pulled from Ollama
    - The model name is invalid or misspelled
    - Ollama service is running but the model isn't installed
    """
    pass


class SummarizationError(OllamaError):
    """Raised when summary generation fails.

    This can occur due to:
    - Network errors communicating with Ollama
    - Model inference errors
    - Invalid or malformed responses from the model
    - Timeout during generation
    """
    pass


# Storage errors
class StorageError(YouTubeSummarizerError):
    """Raised when a database operation fails.

    This exception covers errors such as:
    - Database connection failures
    - SQL query errors
    - Constraint violations
    - File system errors related to the database file
    """
    pass


# Configuration errors
class ConfigurationError(YouTubeSummarizerError):
    """Raised when configuration loading or validation fails.

    This occurs when:
    - Configuration file is missing or malformed
    - Required environment variables are not set
    - Configuration values fail validation
    - Invalid configuration file format
    """
    pass
