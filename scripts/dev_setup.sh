#!/bin/bash
# Development environment setup script for YouTube Summarizer

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  YouTube Summarizer - Development Setup${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$(printf '%s\n' "3.11" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.11" ]; then
    echo -e "${RED}Error: Python 3.11 or higher is required${NC}"
    echo -e "Current version: $(python3 --version)"
    exit 1
fi

echo -e "${GREEN}✓ Python version: $(python3 --version)${NC}\n"

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Skipping creation.${NC}"
else
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}\n"

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip
echo -e "${GREEN}✓ pip upgraded${NC}\n"

# Install project in development mode
echo -e "${YELLOW}Installing project dependencies...${NC}"
pip install -e ".[dev]"
echo -e "${GREEN}✓ Project installed in development mode${NC}\n"

# Create necessary directories
echo -e "${YELLOW}Creating project directories...${NC}"
mkdir -p data
mkdir -p logs
mkdir -p .context-foundry/builder-logs
echo -e "${GREEN}✓ Directories created${NC}\n"

# Create .env.example if it doesn't exist
if [ ! -f ".env.example" ]; then
    echo -e "${YELLOW}Creating .env.example...${NC}"
    cat > .env.example << 'EOF'
# Ollama Configuration
YTS_OLLAMA_HOST=http://localhost:11434
YTS_DEFAULT_MODEL=llama3.1:8b

# Database Configuration
YTS_DATABASE_PATH=./data/summaries.db

# Logging Configuration
YTS_LOG_LEVEL=INFO
YTS_LOG_FILE=./logs/app.log

# Output Configuration
YTS_OUTPUT_FORMAT=rich
EOF
    echo -e "${GREEN}✓ .env.example created${NC}\n"
fi

# Create config.example.yaml if it doesn't exist
if [ ! -f "config.example.yaml" ]; then
    echo -e "${YELLOW}Creating config.example.yaml...${NC}"
    cat > config.example.yaml << 'EOF'
# YouTube Summarizer Configuration Example
# Copy this file to config.yaml and customize as needed

ollama:
  host: http://localhost:11434
  default_model: llama3.1:8b
  timeout: 300
  fallback_models:
    - qwen2.5:7b
    - mistral:7b

database:
  path: ./data/summaries.db

summarization:
  max_chunk_size: 4000
  chunk_overlap: 200
  temperature: 0.7

output:
  format: rich  # 'rich' or 'plain'
  verbose: false

logging:
  level: INFO
  file: ./logs/app.log
EOF
    echo -e "${GREEN}✓ config.example.yaml created${NC}\n"
fi

# Install pre-commit hooks (if .pre-commit-config.yaml exists)
if [ -f ".pre-commit-config.yaml" ]; then
    echo -e "${YELLOW}Installing pre-commit hooks...${NC}"
    if command -v pre-commit &> /dev/null; then
        pre-commit install
        echo -e "${GREEN}✓ Pre-commit hooks installed${NC}\n"
    else
        echo -e "${YELLOW}pre-commit not found in PATH. Skipping hook installation.${NC}\n"
    fi
fi

# Check if Ollama is running
echo -e "${YELLOW}Checking Ollama service...${NC}"
if curl -s -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠ Ollama is not running on localhost:11434${NC}"
    echo -e "${YELLOW}  To install Ollama: https://ollama.ai/download${NC}"
    echo -e "${YELLOW}  Or use Docker: cd docker && docker-compose up -d ollama${NC}"
fi

echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}  Development environment setup complete!${NC}"
echo -e "${GREEN}================================================${NC}\n"

echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Copy .env.example to .env and customize if needed"
echo -e "  2. Copy config.example.yaml to config.yaml and customize"
echo -e "  3. Ensure Ollama is running and pull required models:"
echo -e "     ${YELLOW}ollama pull llama3.1:8b${NC}"
echo -e "     ${YELLOW}ollama pull qwen2.5:7b${NC}"
echo -e "  4. Run tests: ${YELLOW}pytest${NC}"
echo -e "  5. Try the CLI: ${YELLOW}yts --help${NC}\n"

echo -e "${YELLOW}To activate the virtual environment in the future:${NC}"
echo -e "  ${YELLOW}source .venv/bin/activate${NC}\n"
