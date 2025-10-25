"""Configuration management for YouTube Summarizer.

This module provides type-safe configuration management using pydantic-settings.
Configuration values can be loaded from:
1. Environment variables (highest priority, prefixed with YTS_)
2. .env file
3. Default values (lowest priority)

Example:
    Basic usage:
        >>> from youtube_summarizer.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.ollama_host)
        http://localhost:11434

    Environment variable override:
        $ export YTS_OLLAMA_HOST=http://custom-host:11434
        $ python your_script.py

    Using .env file:
        Create a .env file in project root:
        YTS_OLLAMA_HOST=http://custom-host:11434
        YTS_DEFAULT_MODEL=llama3.1:8b
"""

from pathlib import Path
from typing import Optional
import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration with validation.

    All settings can be overridden via environment variables with YTS_ prefix.
    For example, to override ollama_host, set YTS_OLLAMA_HOST environment variable.

    Attributes:
        ollama_host: URL of the Ollama API server
        default_model: Default Ollama model to use for summarization
        api_timeout: Timeout for Ollama API requests in seconds
        database_path: Path to SQLite database file
        summary_max_length: Maximum tokens to generate for summaries
        summary_temperature: Temperature parameter for LLM generation (0.0-1.0)
        preferred_languages: List of preferred transcript languages (ISO 639-1 codes)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None to disable file logging)
        output_format: CLI output format ('rich' or 'plain')
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="YTS_",  # Environment variables: YTS_OLLAMA_HOST, etc.
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env
    )

    # Ollama configuration
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="URL of the Ollama API server",
    )
    default_model: str = Field(
        default="llama3.1:8b",
        description="Default Ollama model to use for summarization",
    )
    api_timeout: int = Field(
        default=300,
        ge=1,
        le=3600,
        description="Timeout for Ollama API requests in seconds",
    )

    # Database configuration
    database_path: str = Field(
        default=str(Path.home() / ".local" / "share" / "youtube-summarizer" / "summaries.db"),
        description="Path to SQLite database file",
    )

    # Summarization settings
    summary_max_length: int = Field(
        default=500,
        ge=50,
        le=4096,
        description="Maximum tokens to generate for summaries",
    )
    summary_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature parameter for LLM generation (0.0-2.0)",
    )

    # Transcript settings
    preferred_languages: list[str] = Field(
        default=["en"],
        description="List of preferred transcript languages (ISO 639-1 codes)",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_file: Optional[str] = Field(
        default="./data/app.log",
        description="Path to log file (None to disable file logging)",
    )

    # CLI output
    output_format: str = Field(
        default="rich",
        description="CLI output format ('rich' or 'plain')",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values.

        Args:
            v: Log level string to validate

        Returns:
            Uppercase log level string

        Raises:
            ValueError: If log level is not valid
        """
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"log_level must be one of {valid_levels}, got '{v}'"
            )
        return v_upper

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        """Validate output format is one of the allowed values.

        Args:
            v: Output format string to validate

        Returns:
            Lowercase output format string

        Raises:
            ValueError: If output format is not valid
        """
        valid_formats = ["rich", "plain"]
        v_lower = v.lower()
        if v_lower not in valid_formats:
            raise ValueError(
                f"output_format must be one of {valid_formats}, got '{v}'"
            )
        return v_lower

    @field_validator("preferred_languages")
    @classmethod
    def validate_preferred_languages(cls, v: list[str]) -> list[str]:
        """Validate preferred languages list is not empty.

        Args:
            v: List of language codes to validate

        Returns:
            List of lowercase language codes

        Raises:
            ValueError: If list is empty or contains invalid codes
        """
        if not v:
            raise ValueError("preferred_languages must contain at least one language")

        # Convert all to lowercase for consistency
        v_lower = [lang.lower() for lang in v]

        # Basic validation: language codes should be 2-3 characters
        for lang in v_lower:
            if not (2 <= len(lang) <= 3 and lang.isalpha()):
                raise ValueError(
                    f"Invalid language code: '{lang}'. "
                    "Language codes should be 2-3 letter ISO 639 codes."
                )

        return v_lower

    @property
    def database_path_obj(self) -> Path:
        """Get database path as Path object.

        Returns:
            Path object for the database file
        """
        return Path(self.database_path).expanduser().resolve()

    @property
    def log_file_obj(self) -> Optional[Path]:
        """Get log file path as Path object.

        Returns:
            Path object for the log file, or None if log_file is None
        """
        if self.log_file is None:
            return None
        return Path(self.log_file).expanduser().resolve()

    def ensure_data_directory(self) -> None:
        """Create data directory if it doesn't exist.

        Creates the parent directory for the database file and log file
        to ensure they can be written to.

        Raises:
            OSError: If directory creation fails due to permissions
        """
        # Create database directory
        self.database_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Create log directory if log file is configured
        if self.log_file_obj is not None:
            self.log_file_obj.parent.mkdir(parents=True, exist_ok=True)

    def model_dump_safe(self) -> dict:
        """Return a safe dictionary representation of settings.

        Returns a dictionary of all settings that's safe to log or display.

        Returns:
            Dictionary of settings with all values
        """
        return {
            "ollama_host": self.ollama_host,
            "default_model": self.default_model,
            "api_timeout": self.api_timeout,
            "database_path": str(self.database_path_obj),
            "summary_max_length": self.summary_max_length,
            "summary_temperature": self.summary_temperature,
            "preferred_languages": self.preferred_languages,
            "log_level": self.log_level,
            "log_file": str(self.log_file_obj) if self.log_file_obj else None,
            "output_format": self.output_format,
        }


# Singleton settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance (singleton pattern).

    This function implements a singleton pattern to ensure that settings
    are loaded only once per application runtime. Subsequent calls return
    the same instance.

    Returns:
        Settings instance with loaded configuration

    Example:
        >>> settings = get_settings()
        >>> print(settings.ollama_host)
        http://localhost:11434
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Force reload settings (useful for testing).

    This function forces a reload of the settings, creating a new instance.
    This is primarily useful in testing scenarios where you need to test
    different configurations.

    Returns:
        New Settings instance with reloaded configuration

    Example:
        >>> import os
        >>> os.environ['YTS_LOG_LEVEL'] = 'DEBUG'
        >>> settings = reload_settings()
        >>> print(settings.log_level)
        DEBUG
    """
    global _settings
    _settings = Settings()
    return _settings
