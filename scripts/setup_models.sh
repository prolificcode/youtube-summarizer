#!/bin/bash
# Pull required Ollama models for YouTube Summarizer

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default models to pull
MODELS=("llama3.1:8b" "qwen2.5:7b" "mistral:7b")

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Ollama Model Setup for YouTube Summarizer${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed${NC}"
    echo -e "Please install docker-compose first"
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker/docker-compose.yml" ]; then
    echo -e "${RED}Error: docker/docker-compose.yml not found${NC}"
    echo -e "Please run this script from the project root directory"
    exit 1
fi

# Check if Ollama container is running
echo -e "${YELLOW}Checking Ollama service status...${NC}"
if ! docker ps | grep -q ollama; then
    echo -e "${YELLOW}Ollama container is not running. Starting it now...${NC}"
    cd docker && docker-compose up -d ollama && cd ..
    echo -e "${YELLOW}Waiting for Ollama to be ready...${NC}"
    sleep 10
fi

echo -e "${GREEN}✓ Ollama service is running${NC}\n"

# Pull each model
for model in "${MODELS[@]}"; do
    echo -e "${BLUE}Pulling model: ${model}${NC}"
    echo -e "${YELLOW}This may take several minutes depending on your internet connection...${NC}"

    if docker exec ollama ollama pull "$model"; then
        echo -e "${GREEN}✓ Successfully pulled ${model}${NC}\n"
    else
        echo -e "${RED}✗ Failed to pull ${model}${NC}"
        echo -e "${YELLOW}Continuing with remaining models...${NC}\n"
    fi
done

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Model setup complete!${NC}"
echo -e "${GREEN}================================================${NC}\n"

# List installed models
echo -e "${BLUE}Installed models:${NC}"
docker exec ollama ollama list

echo -e "\n${YELLOW}You can now use the YouTube Summarizer with these models.${NC}"
echo -e "${YELLOW}Example: docker-compose exec app yts summarize <url> --model llama3.1:8b${NC}\n"
