#!/bin/bash
# Docker entrypoint script for YouTube Summarizer

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting YouTube Summarizer...${NC}"

# Check if Ollama service is accessible
echo -e "${YELLOW}Checking Ollama connection...${NC}"
if curl -s -f "${YTS_OLLAMA_HOST:-http://ollama:11434}/api/tags" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama service is accessible${NC}"
else
    echo -e "${RED}✗ Warning: Ollama service not accessible at ${YTS_OLLAMA_HOST:-http://ollama:11434}${NC}"
    echo -e "${YELLOW}  The application may not function correctly until Ollama is running${NC}"
fi

# Initialize database if it doesn't exist
if [ ! -f "${YTS_DATABASE_PATH:-/app/data/summaries.db}" ]; then
    echo -e "${YELLOW}Initializing database...${NC}"
    mkdir -p "$(dirname "${YTS_DATABASE_PATH:-/app/data/summaries.db}")"
    echo -e "${GREEN}✓ Database directory ready${NC}"
else
    echo -e "${GREEN}✓ Database exists${NC}"
fi

# Print configuration
echo -e "\n${GREEN}Configuration:${NC}"
echo -e "  Ollama Host: ${YTS_OLLAMA_HOST:-http://ollama:11434}"
echo -e "  Default Model: ${YTS_DEFAULT_MODEL:-llama3.1:8b}"
echo -e "  Database Path: ${YTS_DATABASE_PATH:-/app/data/summaries.db}"
echo -e "  Log Level: ${YTS_LOG_LEVEL:-INFO}\n"

# Execute the command passed to the container
exec "$@"
