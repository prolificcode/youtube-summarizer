"""Test suite for YouTube Summarizer.

This package contains comprehensive tests for the YouTube Summarizer application:

- unit/: Fast unit tests with mocked dependencies
- integration/: Integration tests requiring external services (YouTube API, Ollama)
- cli/: CLI command tests using Typer's CliRunner

Run with:
    pytest                          # All tests
    pytest tests/unit/              # Unit tests only
    pytest -m integration           # Integration tests only
    pytest -m "not integration"     # Skip integration tests
"""
