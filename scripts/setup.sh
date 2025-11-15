#!/bin/bash
# Setup script for Network Monitoring System
#
# This script helps you set up the monitoring system for the first time.

set -e

echo "========================================="
echo "  Network Monitoring System - Setup"
echo "========================================="
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo
    echo "⚠️  IMPORTANT: You must edit .env and configure:"
    echo "   - DISCORD_WEBHOOK_URL"
    echo "   - LLM_API_URL"
    echo "   - LLM_API_KEY"
    echo
    echo "Do you want to edit .env now? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    else
        echo "⚠️  Remember to edit .env before starting the system!"
        echo
    fi
else
    echo "✅ .env file already exists"
    echo
fi

# Check if example config exists
if [ ! -f config/hosts.yaml ]; then
    if [ -f config/hosts.yaml.example ]; then
        echo "📝 Do you want to create config/hosts.yaml from example? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            cp config/hosts.yaml.example config/hosts.yaml
            echo "✅ config/hosts.yaml created"
            echo "⚠️  Remember to edit config/hosts.yaml and configure your hosts!"
            echo
        fi
    fi
else
    echo "✅ config/hosts.yaml already exists"
    echo
fi

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data logs
echo "✅ Directories created"
echo

# Build Docker images
echo "🔨 Building Docker images..."
if docker compose version &> /dev/null; then
    docker compose build
else
    docker-compose build
fi
echo "✅ Docker images built"
echo

# Initialize database
echo "🗄️  Initializing database..."
if docker compose version &> /dev/null; then
    docker compose run --rm api python -c "from src.database import init_db; init_db(); print('Database initialized')"
else
    docker-compose run --rm api python -c "from src.database import init_db; init_db(); print('Database initialized')"
fi
echo "✅ Database initialized"
echo

echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo
echo "Next steps:"
echo
echo "1. Edit .env and configure required settings (if not done)"
echo
echo "2. Configure hosts:"
echo "   a) Edit config/hosts.yaml, OR"
echo "   b) Use the API to add hosts dynamically"
echo
echo "3. Start the system:"
if docker compose version &> /dev/null; then
    echo "   docker compose up -d"
else
    echo "   docker-compose up -d"
fi
echo
echo "4. View logs:"
if docker compose version &> /dev/null; then
    echo "   docker compose logs -f"
else
    echo "   docker-compose logs -f"
fi
echo
echo "5. Access the dashboard:"
echo "   http://localhost:8080/api/v1/dashboard"
echo
echo "6. Register a host:"
echo "   python scripts/add-host.py --name 'My Server' --host-id myserver --frequency 300"
echo
echo "========================================="
