#!/bin/bash
set -e

echo "🦞 ClawBot DSGVO MVP Setup"
echo "=========================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env

    # Generate encryption key
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "")
    if [ ! -z "$ENCRYPTION_KEY" ]; then
        sed -i.bak "s|your-32-byte-encryption-key-here-change-me|$ENCRYPTION_KEY|g" .env
        rm .env.bak 2>/dev/null || true
        echo "✅ Generated encryption key"
    else
        echo "⚠️  Could not generate encryption key automatically. Please update .env manually."
    fi
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p core/api core/models core/pipeline scripts dashboard templates

# Build and start services
echo "🐋 Starting Docker services..."
docker compose down -v 2>/dev/null || true
docker compose build
docker compose up -d

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker compose exec -T clawbot-db pg_isready -U clawbot > /dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL is ready"

# Wait for core service to be healthy
echo "⏳ Waiting for ClawBot Core to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo "✅ ClawBot Core is ready"
        break
    fi
    sleep 2
done

# Pull Ollama model
echo "🤖 Pulling Ollama model (qwen2.5:3b)..."
docker compose exec -T clawbot-llm ollama pull qwen2.5:3b

echo ""
echo "✅ ClawBot MVP is ready!"
echo ""
echo "📊 Dashboard: http://localhost:8443"
echo "🔌 API:       http://localhost:8000"
echo "📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "Run health check with: curl http://localhost:8000/api/v1/health"
echo ""

# Open browser on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:8443
fi
