"""Typer CLI application for YouTube Summarizer.

This module implements the command-line interface using Typer and Rich,
providing commands for summarizing videos, listing summaries, searching, and viewing details.
"""

import sys
from typing import Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from youtube_summarizer.config import get_settings
from youtube_summarizer.core.transcript import TranscriptService
from youtube_summarizer.core.summarizer import SummarizerService
from youtube_summarizer.core.storage import StorageService
from youtube_summarizer.core.exceptions import (
    YouTubeSummarizerError,
    TranscriptNotAvailableError,
    InvalidVideoURLError,
    OllamaError,
    ModelNotFoundError,
    StorageError,
)
from youtube_summarizer.cli.utils import extract_video_metadata
from youtube_summarizer.cli.formatters import (
    format_video_table,
    format_summary_detail,
    format_error,
    format_success,
    format_info,
    format_warning,
)

# Initialize Typer app
app = typer.Typer(
    name="yts",
    help="YouTube Video Summarizer - AI-powered video summarization using local LLMs",
    add_completion=False,
)

# Initialize Rich console
console = Console()


def get_storage_service() -> StorageService:
    """Initialize and return storage service with connection.

    Returns:
        Connected StorageService instance

    Raises:
        typer.Exit: If storage initialization fails
    """
    settings = get_settings()
    storage = StorageService(settings.database_path)

    try:
        storage.connect()
        storage.initialize()
        return storage
    except StorageError as e:
        console.print(format_error(
            "Database Error",
            str(e),
            "Check database path and permissions in configuration"
        ))
        raise typer.Exit(code=1)


@app.command()
def summarize(
    url: str = typer.Argument(..., help="YouTube video URL or video ID"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Ollama model to use (overrides default)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-summarization if already exists"),
) -> None:
    """Summarize a YouTube video using local LLM.

    Fetches the video transcript and generates a summary using Ollama.
    The summary is saved to the database for later retrieval.

    Examples:
        yts summarize https://youtube.com/watch?v=dQw4w9WgXcQ
        yts summarize dQw4w9WgXcQ --model llama3.1:8b
        yts summarize https://youtu.be/dQw4w9WgXcQ --force
    """
    settings = get_settings()
    storage = get_storage_service()

    try:
        # Step 1: Extract video metadata
        console.print(format_info("Extracting video metadata..."))
        metadata = extract_video_metadata(url)
        console.print(format_success(f"Found: {metadata.title}"))

        # Check if already summarized
        existing = storage.get_video_by_id(metadata.video_id)
        if existing and not force:
            console.print(format_warning(
                f"Video already summarized. Use --force to re-summarize."
            ))
            console.print(format_info(f"Use 'yts view {metadata.video_id}' to see the summary"))
            raise typer.Exit(code=0)

        # Step 2: Fetch transcript
        console.print(format_info("Fetching transcript..."))
        transcript_service = TranscriptService(settings.preferred_languages)
        transcript = transcript_service.fetch_transcript(metadata.video_id)
        console.print(format_success(f"Retrieved transcript ({len(transcript.segments)} segments)"))

        # Step 3: Generate summary
        model_name = model or settings.default_model
        console.print(format_info(f"Generating summary with {model_name}..."))

        summarizer = SummarizerService(settings)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Summarizing...", total=None)
            summary = summarizer.summarize(transcript, metadata, model_name=model_name)
            progress.update(task, completed=True)

        gen_time = summary.generation_time_seconds or 0
        console.print(format_success(f"Summary generated in {gen_time:.1f}s"))

        # Step 4: Save to database
        console.print(format_info("Saving to database..."))
        video_id = storage.save_video(metadata)
        storage.save_summary(summary, video_id)
        console.print(format_success("Summary saved successfully"))

        # Display the summary
        console.print("\n")
        video_record = storage.get_video_by_id(metadata.video_id)
        if video_record:
            format_summary_detail(video_record, console)

    except InvalidVideoURLError as e:
        console.print(format_error(
            "Invalid URL",
            str(e),
            "Provide a valid YouTube URL or 11-character video ID"
        ))
        raise typer.Exit(code=1)
    except TranscriptNotAvailableError as e:
        console.print(format_error(
            "Transcript Unavailable",
            str(e),
            "Try a different video or check if captions are available"
        ))
        raise typer.Exit(code=1)
    except ModelNotFoundError as e:
        console.print(format_error(
            "Model Not Found",
            str(e),
            f"Run 'ollama pull {model or settings.default_model}' to download the model"
        ))
        raise typer.Exit(code=1)
    except OllamaError as e:
        console.print(format_error(
            "Ollama Error",
            str(e),
            "Ensure Ollama is running: 'ollama serve'"
        ))
        raise typer.Exit(code=1)
    except YouTubeSummarizerError as e:
        console.print(format_error("Error", str(e)))
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(format_error("Unexpected Error", str(e)))
        raise typer.Exit(code=1)
    finally:
        storage.close()


@app.command()
def list(
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum number of videos to show"),
    offset: int = typer.Option(0, "--offset", "-o", help="Number of videos to skip"),
) -> None:
    """List all summarized videos.

    Displays a table of all videos that have been summarized, including
    title, channel, duration, model used, and date.

    Examples:
        yts list
        yts list --limit 10
        yts list --limit 10 --offset 10
    """
    storage = get_storage_service()

    try:
        videos = storage.list_videos(limit=limit, offset=offset)

        if not videos:
            console.print(format_info("No summarized videos found"))
            console.print("Use 'yts summarize <url>' to summarize your first video")
            raise typer.Exit(code=0)

        format_video_table(videos, console)

        # Show pagination info
        total = storage.count_videos()
        shown = min(limit, len(videos))
        console.print(f"\n[dim]Showing {shown} of {total} videos[/dim]")

        if offset + limit < total:
            next_offset = offset + limit
            console.print(f"[dim]Use --offset {next_offset} to see more[/dim]")

    except StorageError as e:
        console.print(format_error("Database Error", str(e)))
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(format_error("Unexpected Error", str(e)))
        raise typer.Exit(code=1)
    finally:
        storage.close()


@app.command()
def view(
    video_id: str = typer.Argument(..., help="Video ID (11 characters) or database row ID"),
) -> None:
    """View detailed summary for a specific video.

    Displays complete video information and summary including metadata,
    model used, generation time, and full summary text.

    Examples:
        yts view dQw4w9WgXcQ
        yts view 1
    """
    storage = get_storage_service()

    try:
        # Try as video ID first (11 characters)
        if len(video_id) == 11:
            video = storage.get_video_by_id(video_id)
        else:
            # Try as database ID
            try:
                db_id = int(video_id)
                video = storage.get_video_by_db_id(db_id)
            except ValueError:
                console.print(format_error(
                    "Invalid ID",
                    "Video ID must be 11 characters or a valid database ID number"
                ))
                raise typer.Exit(code=1)

        if not video:
            console.print(format_error(
                "Video Not Found",
                f"No video found with ID: {video_id}"
            ))
            console.print("Use 'yts list' to see all summarized videos")
            raise typer.Exit(code=1)

        format_summary_detail(video, console)

    except StorageError as e:
        console.print(format_error("Database Error", str(e)))
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(format_error("Unexpected Error", str(e)))
        raise typer.Exit(code=1)
    finally:
        storage.close()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query for video titles and summaries"),
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum number of results"),
) -> None:
    """Search summarized videos by title or summary content.

    Performs a case-insensitive search across video titles, channel names,
    and summary text. Results are ordered by relevance.

    Examples:
        yts search "machine learning"
        yts search python --limit 10
    """
    storage = get_storage_service()

    try:
        videos = storage.search_videos(query, limit=limit)

        if not videos:
            console.print(format_info(f"No videos found matching: {query}"))
            console.print("Try a different search term or use 'yts list' to see all videos")
            raise typer.Exit(code=0)

        console.print(f"[bold]Search results for:[/bold] {query}\n")
        format_video_table(videos, console)
        console.print(f"\n[dim]Found {len(videos)} result(s)[/dim]")

    except StorageError as e:
        console.print(format_error("Database Error", str(e)))
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(format_error("Unexpected Error", str(e)))
        raise typer.Exit(code=1)
    finally:
        storage.close()


@app.command()
def config() -> None:
    """Display current configuration settings.

    Shows all configuration values including Ollama settings, database path,
    and summarization parameters. Indicates which values are using defaults
    vs. custom settings.
    """
    settings = get_settings()

    config_info = f"""[bold blue]Current Configuration[/bold blue]

[bold]Ollama Settings:[/bold]
  Host: {settings.ollama_host}
  Default Model: {settings.default_model}
  API Timeout: {settings.api_timeout}s

[bold]Database:[/bold]
  Path: {settings.database_path}

[bold]Summarization:[/bold]
  Max Length: {settings.summary_max_length} tokens
  Temperature: {settings.summary_temperature}

[bold]Transcript:[/bold]
  Preferred Languages: {', '.join(settings.preferred_languages)}

[dim]To override settings, set environment variables with YTS_ prefix
or create a .env file in the project root.[/dim]
"""

    console.print(config_info)


@app.command()
def version() -> None:
    """Show version information."""
    from youtube_summarizer import __version__
    console.print(f"YouTube Summarizer v{__version__}")


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
