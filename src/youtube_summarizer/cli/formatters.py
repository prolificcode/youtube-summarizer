"""Rich output formatting for CLI.

This module provides beautiful terminal output formatting using the Rich library.
Includes table formatting for video lists, detailed summary panels, and error displays.
"""

from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text

from youtube_summarizer.core.models import VideoRecord


def format_video_table(videos: list[VideoRecord], console: Console) -> None:
    """Display videos in a formatted table.

    Creates a beautiful table showing video information including ID, title,
    channel, duration, model used, and date. Automatically truncates long titles
    to fit within table constraints.

    Args:
        videos: List of VideoRecord objects to display
        console: Rich Console instance for output

    Example:
        >>> from rich.console import Console
        >>> console = Console()
        >>> format_video_table(videos, console)
    """
    table = Table(
        title="Summarized Videos",
        show_header=True,
        header_style="bold magenta",
        border_style="blue"
    )

    table.add_column("Video ID", style="cyan", width=12, no_wrap=True)
    table.add_column("Title", style="white", width=40)
    table.add_column("Channel", style="green", width=20)
    table.add_column("Duration", style="yellow", width=10, justify="right")
    table.add_column("Model", style="blue", width=15)
    table.add_column("Date", style="dim", width=12)

    for video in videos:
        # Format duration
        if video.duration_seconds:
            minutes = video.duration_seconds // 60
            seconds = video.duration_seconds % 60
            duration = f"{minutes}m {seconds}s" if minutes < 60 else f"{minutes//60}h {minutes%60}m"
        else:
            duration = "N/A"

        # Get model name from most recent summary
        model = video.summaries[0].model_name if video.summaries else "N/A"

        # Format date
        date = video.created_at.strftime("%Y-%m-%d") if video.created_at else "N/A"

        # Truncate title if too long
        title = video.title
        if len(title) > 40:
            title = title[:37] + "..."

        # Truncate channel name if too long
        channel = video.channel_name or "Unknown"
        if len(channel) > 20:
            channel = channel[:17] + "..."

        table.add_row(
            video.video_id,
            title,
            channel,
            duration,
            model,
            date
        )

    console.print(table)


def format_summary_detail(video: VideoRecord, console: Console) -> None:
    """Display detailed video summary.

    Shows comprehensive information about a video including metadata
    panel and summary panel with generation details. Uses Markdown
    rendering for the summary text.

    Args:
        video: VideoRecord with summary information
        console: Rich Console instance for output

    Example:
        >>> from rich.console import Console
        >>> console = Console()
        >>> format_summary_detail(video, console)
    """
    # Format duration
    if video.duration_seconds:
        hours, remainder = divmod(video.duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            duration_str = f"{hours}h {minutes}m {seconds}s"
        else:
            duration_str = f"{minutes}m {seconds}s"
    else:
        duration_str = "Unknown"

    # Video information panel
    info_lines = [
        f"[bold]Title:[/bold] {video.title}",
        f"[bold]Channel:[/bold] {video.channel_name or 'Unknown'}",
        f"[bold]Duration:[/bold] {duration_str}",
        f"[bold]URL:[/bold] {video.url}",
        f"[bold]Video ID:[/bold] {video.video_id}",
    ]

    if video.publish_date:
        info_lines.insert(3, f"[bold]Published:[/bold] {video.publish_date}")

    info_text = "\n".join(info_lines)

    console.print(Panel(
        info_text,
        title="[bold blue]Video Information[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    ))

    # Summary panel
    if video.summaries:
        latest_summary = video.summaries[0]

        # Format generation time
        gen_time = (
            f"{latest_summary.generation_time_seconds:.1f}s"
            if latest_summary.generation_time_seconds
            else "N/A"
        )

        # Format creation timestamp
        created = (
            latest_summary.created_at.strftime('%Y-%m-%d %H:%M:%S')
            if latest_summary.created_at
            else 'N/A'
        )

        # Build summary metadata
        summary_meta = [
            f"[bold]Model:[/bold] {latest_summary.model_name}",
            f"[bold]Generated:[/bold] {created}",
            f"[bold]Generation Time:[/bold] {gen_time}",
        ]

        if latest_summary.token_count:
            summary_meta.append(f"[bold]Tokens:[/bold] {latest_summary.token_count}")

        summary_meta_text = "\n".join(summary_meta)

        # Create summary content with metadata and text
        summary_content = f"{summary_meta_text}\n\n[dim]{'─' * 70}[/dim]\n\n{latest_summary.summary_text}"

        console.print(Panel(
            summary_content,
            title="[bold green]Summary[/bold green]",
            border_style="green",
            padding=(1, 2)
        ))

        # Show number of summaries if multiple
        if len(video.summaries) > 1:
            console.print(
                f"\n[dim]Note: This video has {len(video.summaries)} summaries. "
                f"Showing the most recent.[/dim]"
            )
    else:
        console.print(Panel(
            "[yellow]No summary available for this video[/yellow]",
            border_style="yellow"
        ))


def format_error(title: str, message: str, suggestion: Optional[str] = None) -> Panel:
    """Format error message as a Rich panel.

    Creates a visually distinct error panel with title, message, and optional
    suggestion for resolution.

    Args:
        title: Error title/category
        message: Detailed error message
        suggestion: Optional suggestion for fixing the error

    Returns:
        Rich Panel object ready for display

    Example:
        >>> panel = format_error("Connection Failed", "Could not connect to Ollama")
        >>> console.print(panel)
    """
    error_content = f"[red]{message}[/red]"

    if suggestion:
        error_content += f"\n\n[yellow]Suggestion:[/yellow] {suggestion}"

    return Panel(
        error_content,
        title=f"[bold red]❌ {title}[/bold red]",
        border_style="red",
        padding=(1, 2)
    )


def format_success(message: str) -> Text:
    """Format success message with checkmark.

    Args:
        message: Success message to display

    Returns:
        Rich Text object with formatted success message

    Example:
        >>> text = format_success("Summary generated successfully")
        >>> console.print(text)
    """
    return Text.from_markup(f"[green]✓[/green] {message}")


def format_info(message: str) -> Text:
    """Format informational message.

    Args:
        message: Info message to display

    Returns:
        Rich Text object with formatted info message

    Example:
        >>> text = format_info("Processing video...")
        >>> console.print(text)
    """
    return Text.from_markup(f"[blue]ℹ[/blue] {message}")


def format_warning(message: str) -> Text:
    """Format warning message.

    Args:
        message: Warning message to display

    Returns:
        Rich Text object with formatted warning message

    Example:
        >>> text = format_warning("Video already summarized")
        >>> console.print(text)
    """
    return Text.from_markup(f"[yellow]⚠[/yellow] {message}")


def create_progress_bar(console: Console):
    """Create a Rich progress bar for long-running operations.

    Args:
        console: Rich Console instance

    Returns:
        Rich Progress instance configured for task tracking

    Example:
        >>> from rich.console import Console
        >>> console = Console()
        >>> progress = create_progress_bar(console)
        >>> with progress:
        ...     task = progress.add_task("Processing...", total=100)
        ...     # do work
        ...     progress.update(task, advance=10)
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    )
