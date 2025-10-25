"""Ollama LLM integration for video summarization.

This module provides functionality to generate summaries of YouTube video transcripts
using Ollama's local LLM API. It handles long transcripts via chunking, manages model
availability, and tracks generation performance.
"""

import time
from typing import Optional

import ollama

from youtube_summarizer.core.models import Summary, VideoMetadata, Transcript
from youtube_summarizer.core.exceptions import (
    OllamaError,
    ModelNotFoundError,
    SummarizationError,
)
from youtube_summarizer.config import Settings


# Prompt template for summarization (version 1)
SUMMARY_PROMPT_V1 = """You are an expert at summarizing YouTube video content.

Video Title: {title}
Channel: {channel}
Duration: {duration}

Transcript:
{transcript}

Task: Create a concise summary (3-5 paragraphs) that captures:
1. Main topic and purpose of the video
2. Key points and arguments presented
3. Important conclusions or takeaways

Keep the summary clear, objective, and informative. Avoid redundancy.

Summary:"""


class SummarizerService:
    """Service for generating video summaries using Ollama.

    This service manages the interaction with Ollama's LLM API to generate
    summaries of video transcripts. It handles model availability checking,
    automatic chunking of long transcripts, and performance tracking.

    Attributes:
        settings: Application settings containing Ollama configuration
        client: Ollama API client instance
        max_context_tokens: Maximum tokens for model context window

    Example:
        >>> from youtube_summarizer.config import get_settings
        >>> settings = get_settings()
        >>> service = SummarizerService(settings)
        >>> summary = service.summarize(transcript, metadata)
        >>> print(summary.summary_text)
    """

    def __init__(self, settings: Settings):
        """Initialize the summarizer service.

        Args:
            settings: Application settings (Ollama host, default model, etc.)
        """
        self.settings = settings
        self.client = ollama.Client(host=settings.ollama_host)
        self.max_context_tokens = 3000  # Safe limit for most 7B-8B models

    def ensure_model_available(
        self,
        model_name: str,
        auto_pull: bool = False
    ) -> bool:
        """Check if model is available, optionally pull if missing.

        Args:
            model_name: Model identifier (e.g., "llama3.1:8b")
            auto_pull: If True, automatically pull missing model

        Returns:
            True if model is available or was successfully pulled

        Raises:
            ModelNotFoundError: Model not available and auto_pull=False
            OllamaError: Ollama API error (connection failed, etc.)

        Example:
            >>> service = SummarizerService(settings)
            >>> service.ensure_model_available("llama3.1:8b", auto_pull=True)
            True
        """
        try:
            models_response = self.client.list()
            available_models = [m.model for m in models_response.models]

            if model_name in available_models:
                return True

            if auto_pull:
                print(f"Pulling model {model_name}...")
                self.client.pull(model_name)
                return True
            else:
                raise ModelNotFoundError(
                    f"Model '{model_name}' not found. "
                    f"Available models: {', '.join(available_models)}"
                )

        except ModelNotFoundError:
            raise
        except Exception as e:
            raise OllamaError(f"Failed to check model availability: {str(e)}")

    def estimate_tokens(self, text: str) -> int:
        """Rough estimation of token count.

        Uses a simple heuristic: 4 characters ≈ 1 token
        For precise counting, would need tiktoken, but this is good enough
        for our chunking purposes.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated number of tokens

        Example:
            >>> service = SummarizerService(settings)
            >>> service.estimate_tokens("Hello world")
            2
        """
        return len(text) // 4

    def chunk_transcript(
        self,
        transcript: str,
        max_tokens: Optional[int] = None
    ) -> list[str]:
        """Split long transcript into chunks for processing.

        Uses overlapping chunks (10% overlap) to maintain context between
        chunks and avoid cutting off sentences mid-thought.

        Args:
            transcript: Full transcript text
            max_tokens: Maximum tokens per chunk (default: self.max_context_tokens)

        Returns:
            List of transcript chunks, each within the token limit

        Example:
            >>> service = SummarizerService(settings)
            >>> chunks = service.chunk_transcript(long_transcript, max_tokens=1000)
            >>> print(f"Split into {len(chunks)} chunks")
        """
        max_tokens = max_tokens or self.max_context_tokens
        max_chars = max_tokens * 4  # Rough conversion
        overlap_chars = max_chars // 10  # 10% overlap

        chunks = []
        start = 0

        while start < len(transcript):
            end = start + max_chars

            # Try to break at sentence boundary
            if end < len(transcript):
                # Look for period within last 200 chars
                period_pos = transcript.rfind('.', end - 200, end)
                if period_pos > start:
                    end = period_pos + 1

            chunks.append(transcript[start:end])
            start = end - overlap_chars

        return chunks

    def summarize_chunk(
        self,
        chunk: str,
        metadata: VideoMetadata,
        model_name: str,
        prompt_template: str = SUMMARY_PROMPT_V1
    ) -> str:
        """Summarize a single transcript chunk.

        Args:
            chunk: Transcript text to summarize
            metadata: Video metadata for context
            model_name: Ollama model to use
            prompt_template: Prompt template string with placeholders

        Returns:
            Summary text for this chunk

        Raises:
            SummarizationError: Summarization failed

        Example:
            >>> service = SummarizerService(settings)
            >>> summary = service.summarize_chunk(
            ...     chunk_text, metadata, "llama3.1:8b"
            ... )
        """
        prompt = prompt_template.format(
            title=metadata.title,
            channel=metadata.channel_name or "Unknown",
            duration=metadata.duration_formatted,
            transcript=chunk
        )

        try:
            response = self.client.generate(
                model=model_name,
                prompt=prompt,
                options={
                    'temperature': self.settings.summary_temperature,
                    'top_p': 0.9,
                    'num_predict': self.settings.summary_max_length,
                }
            )

            return response['response'].strip()

        except Exception as e:
            raise SummarizationError(f"Summarization failed: {str(e)}")

    def summarize(
        self,
        transcript: Transcript,
        metadata: VideoMetadata,
        model_name: Optional[str] = None
    ) -> Summary:
        """Generate summary for video transcript.

        Automatically handles long transcripts via chunking. If the transcript
        exceeds the context window, it will be split into chunks, each summarized
        separately, then combined into a final summary.

        Args:
            transcript: Video transcript
            metadata: Video metadata
            model_name: Model to use (default: settings.default_model)

        Returns:
            Summary object with generated text and metadata

        Raises:
            ModelNotFoundError: Model not available
            SummarizationError: Summarization failed

        Example:
            >>> service = SummarizerService(settings)
            >>> summary = service.summarize(transcript, metadata)
            >>> print(f"Generated in {summary.generation_time_seconds:.2f}s")
            >>> print(summary.summary_text)
        """
        model_name = model_name or self.settings.default_model

        # Ensure model is available
        self.ensure_model_available(model_name)

        start_time = time.time()
        full_transcript = transcript.full_text
        token_estimate = self.estimate_tokens(full_transcript)

        # Handle long transcripts
        if token_estimate > self.max_context_tokens:
            summary_text = self._summarize_long_transcript(
                full_transcript, metadata, model_name
            )
        else:
            summary_text = self.summarize_chunk(
                full_transcript, metadata, model_name
            )

        generation_time = time.time() - start_time

        return Summary(
            video_id=0,  # Will be set by storage layer
            summary_text=summary_text,
            model_name=model_name,
            prompt_version="v1",
            token_count=token_estimate,
            generation_time_seconds=generation_time
        )

    def _summarize_long_transcript(
        self,
        transcript: str,
        metadata: VideoMetadata,
        model_name: str
    ) -> str:
        """Handle transcripts exceeding context window.

        Strategy:
        1. Chunk the transcript into manageable pieces
        2. Summarize each chunk independently
        3. Combine chunk summaries
        4. Generate final consolidated summary

        Args:
            transcript: Full transcript text
            metadata: Video metadata
            model_name: Model to use

        Returns:
            Final consolidated summary text

        Raises:
            SummarizationError: If summarization fails at any stage
        """
        chunks = self.chunk_transcript(transcript)

        # Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks, 1):
            print(f"Summarizing chunk {i}/{len(chunks)}...")
            summary = self.summarize_chunk(chunk, metadata, model_name)
            chunk_summaries.append(summary)

        # Combine chunk summaries
        combined = '\n\n'.join(chunk_summaries)

        # Final consolidation
        final_prompt = f"""Combine the following summaries into a single cohesive summary:

{combined}

Create a unified summary that captures all key points:"""

        try:
            response = self.client.generate(
                model=model_name,
                prompt=final_prompt,
                options={
                    'temperature': self.settings.summary_temperature,
                    'num_predict': self.settings.summary_max_length,
                }
            )
            return response['response'].strip()
        except Exception as e:
            raise SummarizationError(
                f"Failed to combine chunk summaries: {str(e)}"
            )
