#!/bin/bash
# Script to create a production-only branch

set -e

PRODUCTION_BRANCH="production"

echo "Creating production branch with minimal files..."

# Create and switch to production branch
git checkout -b "${PRODUCTION_BRANCH}" 2>/dev/null || git checkout "${PRODUCTION_BRANCH}"

# Remove development files
echo "Removing development files..."

# Development configuration files
git rm -f pyproject.toml pytest.ini .pre-commit-config.yaml 2>/dev/null || true
git rm -f requirements-dev.txt 2>/dev/null || true
git rm -f Dockerfile docker-compose.yml .dockerignore 2>/dev/null || true

# Development directories
git rm -rf tests/ scripts/ 2>/dev/null || true

# Development documentation (keep user-facing README)
git rm -f CLAUDE.md 2>/dev/null || true

# Create production README
cat > README-PRODUCTION.md << 'EOF'
# ECE Competitor Identification Tool

A professional tool for analyzing competitors around early childhood education centers.

## Quick Start

1. **Install Python 3.8+**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Google Maps API key
   ```
4. **Run application:**
   ```bash
   streamlit run app.py
   ```
5. **Open browser:** http://localhost:8501

## Features

- Single location competitor analysis
- Batch analysis via CSV upload
- Interactive maps and visualizations
- Tier-based competitor classification
- CSV export of results

## Requirements

- Python 3.8+
- Google Maps API key (Geocoding + Places APIs)
- Internet connection

## Support

Contact: admin@tuscanystrategy.com

---
© 2024 Tuscany Strategy Consulting
EOF

# Add production README
git add README-PRODUCTION.md

# Commit changes
git commit -m "Create production release branch

- Remove all development files and configurations
- Keep only runtime files needed by end users
- Add production-focused README
- Ready for end-user download and deployment

This branch contains only:
- app.py (main application)
- src/ (source code modules)
- requirements.txt (runtime dependencies)
- .env.example (configuration template)
- README-PRODUCTION.md (user instructions)" 2>/dev/null || echo "No changes to commit"

echo "✅ Production branch '${PRODUCTION_BRANCH}' created!"
echo ""
echo "📦 Production branch contains only:"
git ls-files | grep -E '\.(py|txt|md)$' | head -20

echo ""
echo "🚀 To publish production release:"
echo "   1. Push branch: git push origin ${PRODUCTION_BRANCH}"
echo "   2. Create release from this branch on GitHub"
echo "   3. Users can download: 'Download ZIP' from ${PRODUCTION_BRANCH} branch"

# Switch back to main branch
git checkout main
