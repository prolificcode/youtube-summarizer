# YouTube Summarizer

AI-powered YouTube video summarizer using local LLM models via Ollama. Get concise summaries of any YouTube video without relying on cloud APIs - everything runs locally on your machine with full GPU acceleration support.

## Features

- **Local LLM Summarization**: Uses Ollama for complete privacy and GPU acceleration
- **Automatic Transcript Fetching**: Retrieves YouTube video transcripts automatically
- **Beautiful CLI Interface**: Rich terminal output with tables, panels, and progress indicators
- **SQLite Database**: Stores summaries locally for quick retrieval and searching
- **Multiple Commands**: Summarize, list, search, and view video summaries
- **Docker Support**: Easy deployment on NAS or servers with Docker
- **Modular Architecture**: Clean separation for future web UI expansion

## Prerequisites

- **Python 3.11+**
- **Ollama** - [Install Ollama](https://ollama.com/)
- **Git** (for installation)

### Hardware Requirements

- **Minimum**: 8GB RAM, CPU-only mode
- **Recommended**: 16GB+ RAM, NVIDIA GPU (RTX 3060 or better) for fast summarization
- **This build optimized for**: AMD Ryzen 9 9800X3D + RTX 5080 (but works on any system)

## Quick Start

### 1. Install Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Windows
# Download from https://ollama.com/download
```

### 2. Pull a Model

```bash
# Recommended for quality (requires ~4.7GB)
ollama pull llama3.1:8b

# Or for faster/smaller (requires ~2.7GB)
ollama pull mistral

# Or for best quality (requires ~40GB, needs powerful GPU)
ollama pull llama3.1:70b
```

### 3. Start Ollama Server

```bash
ollama serve
```

### 4. Install YouTube Summarizer

```bash
# Clone the repository
git clone https://github.com/prolificcode/youtube-summarizer.git
cd youtube-summarizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .
```

## Usage

### Summarize a Video

```bash
# Using URL
yts summarize https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Using video ID
yts summarize dQw4w9WgXcQ

# Using specific model
yts summarize dQw4w9WgXcQ --model llama3.1:70b

# Force re-summarization
yts summarize dQw4w9WgXcQ --force
```

### List All Summaries

```bash
# List recent summaries
yts list

# Limit results
yts list --limit 10

# Pagination
yts list --limit 10 --offset 10
```

### Search Summaries

```bash
# Search by keywords
yts search "machine learning"

# Search with limit
yts search python --limit 5
```

### View Summary Details

```bash
# View by video ID
yts view dQw4w9WgXcQ

# View by database ID
yts view 1
```

### Check Configuration

```bash
yts config
```

### Show Version

```bash
yts version
```

## Configuration

Configuration can be customized via environment variables or a `.env` file.

### Environment Variables

All settings can be overridden with `YTS_` prefix:

```bash
export YTS_OLLAMA_HOST=http://localhost:11434
export YTS_DEFAULT_MODEL=llama3.1:8b
export YTS_DATABASE_PATH=./data/summaries.db
export YTS_SUMMARY_TEMPERATURE=0.7
```

### Configuration File

Create a `.env` file in the project root:

```env
YTS_OLLAMA_HOST=http://localhost:11434
YTS_DEFAULT_MODEL=llama3.1:8b
YTS_API_TIMEOUT=300
YTS_DATABASE_PATH=~/.local/share/youtube-summarizer/summaries.db
YTS_SUMMARY_MAX_LENGTH=500
YTS_SUMMARY_TEMPERATURE=0.7
YTS_PREFERRED_LANGUAGES=["en"]
```

### Available Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `YTS_OLLAMA_HOST` | `http://localhost:11434` | Ollama API server URL |
| `YTS_DEFAULT_MODEL` | `llama3.1:8b` | Default LLM model |
| `YTS_API_TIMEOUT` | `300` | API timeout in seconds |
| `YTS_DATABASE_PATH` | `~/.local/share/youtube-summarizer/summaries.db` | SQLite database path |
| `YTS_SUMMARY_MAX_LENGTH` | `500` | Max tokens for summaries |
| `YTS_SUMMARY_TEMPERATURE` | `0.7` | LLM temperature (0.0-2.0) |
| `YTS_PREFERRED_LANGUAGES` | `["en"]` | Preferred transcript languages |

## Docker Deployment

Perfect for running on a NAS or server.

### Build and Run

```bash
cd docker

# Build image
docker build -t youtube-summarizer .

# Run container
docker-compose up -d
```

### Docker Compose

The included `docker-compose.yml` provides:
- Persistent database storage
- GPU support (optional)
- Environment variable configuration
- Volume mounts for data

### GPU Support in Docker

To enable GPU acceleration in Docker:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. Uncomment GPU sections in `docker-compose.yml`
3. Run: `docker-compose up -d`

## Architecture

```
youtube-summarizer/
├── src/youtube_summarizer/
│   ├── cli/              # CLI interface (Typer + Rich)
│   │   ├── app.py        # Main CLI commands
│   │   ├── formatters.py # Output formatting
│   │   └── utils.py      # Helper functions
│   ├── core/             # Business logic (framework-agnostic)
│   │   ├── transcript.py # YouTube transcript fetching
│   │   ├── summarizer.py # Ollama LLM integration
│   │   ├── storage.py    # SQLite database operations
│   │   ├── models.py     # Pydantic data models
│   │   └── exceptions.py # Custom exceptions
│   └── config.py         # Configuration management
├── tests/                # Test suite
├── docker/               # Docker deployment files
└── scripts/              # Utility scripts
```

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src/youtube_summarizer

# Specific test file
pytest tests/unit/test_transcript.py
```

### Code Quality

```bash
# Format code
ruff format src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/
```

## Troubleshooting

### "Ollama connection failed"

**Solution**: Make sure Ollama is running:
```bash
ollama serve
```

### "Model not found"

**Solution**: Pull the model first:
```bash
ollama pull llama3.1:8b
```

### "No transcript available"

**Causes**:
- Video has no captions/subtitles
- Video is private or deleted
- Video is age-restricted

**Solution**: Try a different video that has public captions

### Slow summarization

**Solutions**:
1. Use a smaller model: `ollama pull mistral`
2. Ensure GPU acceleration is working: `ollama ps`
3. Reduce `YTS_SUMMARY_MAX_LENGTH` in configuration

## Roadmap

- [ ] Web UI with FastAPI
- [ ] YouTube OAuth integration for recommendations
- [ ] Automatic periodic summarization
- [ ] Summary export formats (PDF, Markdown)
- [ ] Multi-language support
- [ ] Video chapter detection
- [ ] Sentiment analysis
- [ ] Key quote extraction
- [ ] Topic modeling

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

- **Ollama** - Local LLM inference
- **youtube-transcript-api** - Transcript fetching
- **Typer** - CLI framework
- **Rich** - Terminal formatting
- **Pydantic** - Data validation

## Support

- **Issues**: [GitHub Issues](https://github.com/prolificcode/youtube-summarizer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/prolificcode/youtube-summarizer/discussions)

---

**Built with ❤️ for privacy-conscious YouTube enthusiasts**
