#!/bin/bash
# Setup verification script for ECE Competitor Tool

echo "🔍 Verifying ECE Competitor Tool Setup..."
echo "========================================"

# Check Python version
echo -n "✓ Python 3.8+: "
if command -v python3 &> /dev/null; then
    python3 --version
else
    echo "❌ Not found"
fi

# Check essential files
echo ""
echo "📁 Essential Files:"
files=(".env.example" "requirements.txt" "pyproject.toml" "README.md" "Dockerfile" "docker-compose.yml" ".gitignore")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ❌ $file missing!"
    fi
done

# Check if .env exists
echo ""
echo "🔐 Environment Setup:"
if [ -f ".env" ]; then
    echo "  ✓ .env file exists"
    if grep -q "GOOGLE_MAPS_API_KEY=" .env && ! grep -q "GOOGLE_MAPS_API_KEY=$" .env; then
        echo "  ✓ Google Maps API key appears to be set"
    else
        echo "  ⚠️  Google Maps API key not set in .env"
    fi
else
    echo "  ⚠️  .env file not found (copy from .env.example)"
fi

# Check Docker
echo ""
echo "🐳 Docker Setup:"
if command -v docker &> /dev/null; then
    echo "  ✓ Docker installed"
    if command -v docker-compose &> /dev/null; then
        echo "  ✓ Docker Compose installed"
    else
        echo "  ⚠️  Docker Compose not found"
    fi
else
    echo "  ℹ️  Docker not installed (optional)"
fi

echo ""
echo "========================================"
echo "📚 Quick Start Instructions:"
echo ""
echo "1. Copy .env.example to .env:"
echo "   cp .env.example .env"
echo ""
echo "2. Add your Google Maps API key to .env"
echo ""
echo "3. Choose your setup method:"
echo "   Docker:  docker-compose up"
echo "   Python:  pip install . && streamlit run app.py"
echo ""
echo "For more details, see README.md"
