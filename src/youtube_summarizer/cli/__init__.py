"""CLI interface layer for YouTube Summarizer.

This package provides the command-line interface using Typer and Rich,
including command implementations, output formatting, and utility functions.

Modules:
    app: Typer CLI application with commands (summarize, list, search, view)
    formatters: Rich output formatting for beautiful terminal display
    utils: Utility functions for metadata extraction and CLI helpers
"""

from youtube_summarizer.cli.app import app, main

__all__ = ["app", "main"]
