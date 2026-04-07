#!/bin/bash
# Script to create production release package

set -e

VERSION=${1:-"v1.0.0"}
RELEASE_DIR="ece-tool-release"
PACKAGE_NAME="ece-tool-${VERSION}"

echo "Creating production release package for ${VERSION}..."

# Clean up any existing release directory
rm -rf "${RELEASE_DIR}" "${PACKAGE_NAME}.zip"

# Create release directory
mkdir -p "${RELEASE_DIR}"

# Copy only production files
echo "Copying production files..."

# Main application files
cp app.py "${RELEASE_DIR}/"
cp pyproject.toml "${RELEASE_DIR}/"
cp .env.example "${RELEASE_DIR}/"

# Docker files for container option
cp Dockerfile "${RELEASE_DIR}/"
cp docker-compose.prod.yml "${RELEASE_DIR}/docker-compose.yml"
cp .dockerignore "${RELEASE_DIR}/"

# Copy source code
cp -r src/ "${RELEASE_DIR}/"

# Create production README
cat > "${RELEASE_DIR}/README.md" << 'EOF'
# ECE Competitor Identification Tool

Professional tool for analyzing competitors around early childhood education centers.

**Developed by Tuscany Strategy Consulting**

## ✨ Features

- **Single Location Analysis**: Analyze competitors around one ECE center
- **Batch Analysis**: Upload CSV to analyze multiple locations at once
- **Interactive Maps**: Visual competitor mapping with tier classifications
- **Tier-Based Classification**: Automatic competitor prioritization
- **Professional Reporting**: Export results to CSV for further analysis

## 🚀 Quick Start

### Easiest: Docker (Recommended)
```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and add your Google Maps API key

# 2. Run application
docker-compose up

# 3. Open browser to http://localhost:8501
```

### Alternative: Python Installation
```bash
# 1. Install application
pip install .

# 2. Configure environment
cp .env.example .env
# Edit .env and add your Google Maps API key

# 3. Run application
streamlit run app.py

# 4. Open browser to http://localhost:8501
```

## 📋 Requirements

- Google Maps API key (Geocoding + Places APIs)
- Either Docker OR Python 3.8+
- Internet connection

## 📖 Detailed Instructions

See **INSTALL.md** for complete setup instructions, troubleshooting, and API configuration.

## 🏢 About Tuscany Strategy

We help education leaders make high-stakes decisions with confidence through data-driven competitive intelligence and strategic consulting.

**Contact**: admin@tuscanystrategy.com

---
© 2024 Tuscany Strategy Consulting
EOF

# Create a simplified README for end users
cat > "${RELEASE_DIR}/INSTALL.md" << 'EOF'
# ECE Competitor Identification Tool - Installation Guide

## 🚀 Quick Start Options

### Option 1: Docker (Recommended - Easiest)

1. **Install Docker** if not already installed
2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env file and add your Google Maps API key
   ```
3. **Run with Docker Compose:**
   ```bash
   docker-compose up
   ```
4. **Open browser** to http://localhost:8501

### Option 2: Python Installation

1. **Install Python 3.8+** if not already installed
2. **Install the application:**
   ```bash
   pip install .
   ```
3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env file and add your Google Maps API key
   ```
4. **Run the application:**
   ```bash
   streamlit run app.py
   ```
5. **Open browser** to http://localhost:8501

### Option 3: Development Mode (Advanced)

1. **Install in development mode:**
   ```bash
   pip install -e .
   ```
2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Google Maps API key
   ```
3. **Run application:**
   ```bash
   streamlit run app.py
   ```

## 📋 Requirements

- **Option 1 (Docker)**: Docker and Docker Compose
- **Option 2 (Python)**: Python 3.8+
- **All Options**: Google Maps API key (Geocoding + Places APIs enabled)
- Internet connection for API calls

## 🔑 Google Maps API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Geocoding API** and **Places API**
4. Create API key in Credentials section
5. Add the key to your `.env` file

## 🆘 Troubleshooting

**Port already in use:**
```bash
# Find and kill process on port 8501
lsof -ti:8501 | xargs kill -9
```

**Docker issues:**
```bash
# Rebuild containers
docker-compose down
docker-compose up --build
```

**Python dependency issues:**
```bash
# Upgrade pip first
pip install --upgrade pip
pip install .
```

## 📞 Support

For technical support, contact: admin@tuscanystrategy.com

---
© 2024 Tuscany Strategy Consulting
EOF

# Remove any development artifacts that might have been copied
find "${RELEASE_DIR}" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "${RELEASE_DIR}" -name "*.pyc" -delete 2>/dev/null || true
find "${RELEASE_DIR}" -name ".DS_Store" -delete 2>/dev/null || true

# Create zip package
echo "Creating release package..."
zip -r "${PACKAGE_NAME}.zip" "${RELEASE_DIR}"

# Clean up temporary directory
rm -rf "${RELEASE_DIR}"

echo "✅ Release package created: ${PACKAGE_NAME}.zip"
echo "📦 Package contents:"
unzip -l "${PACKAGE_NAME}.zip"

echo ""
echo "🚀 Ready to upload to GitHub Releases!"
echo "   1. Go to: https://github.com/your-username/ece-tool/releases"
echo "   2. Click 'Create a new release'"
echo "   3. Tag: ${VERSION}"
echo "   4. Upload: ${PACKAGE_NAME}.zip"
