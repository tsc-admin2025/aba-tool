# Installation Guide - ECE Competitor Tool

## Prerequisites

### For Docker Installation (Easiest)
- Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop/))
- A Google Maps API key (see below)

### For Python Installation
- Python 3.8 or higher
- pip package manager
- A Google Maps API key (see below)

## Step-by-Step Installation

### 1. Get the Code

```bash
# Clone from GitHub
git clone https://github.com/tsc-admin2025/ece-tool.git
cd ece-tool

# Or download ZIP from GitHub and extract
```

### 2. Get a Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable these APIs:
   - Geocoding API
   - Places API
   - Routes API
4. Create credentials → API Key
5. (Optional) Restrict key to these APIs for security

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# Replace YOUR_API_KEY_HERE with your actual key
```

**For detailed step-by-step instructions on getting and setting up your Google Maps API key, see [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md)**

### 4. Run the Application

#### Option A: Using Docker (Recommended)

```bash
# Start the application
docker-compose up

# To run in background:
docker-compose up -d

# To stop:
docker-compose down
```

#### Option B: Using Python

```bash
# Install dependencies
pip install .

# Or using requirements.txt:
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### 5. Access the Application

Open your web browser and go to:
- http://localhost:8501

## Troubleshooting

### Common Issues

**"Invalid API key" error**
- Check your .env file has the correct API key
- Ensure the required Google APIs are enabled
- Check API key restrictions

**Port 8501 already in use**
- Stop any other Streamlit apps
- Or change port: `streamlit run app.py --server.port 8502`

**Docker connection errors**
- Ensure Docker Desktop is running
- Try: `docker-compose down` then `docker-compose up --build`

**Module import errors (Python)**
- Ensure you're in the project directory
- Try: `pip install -e .` for development mode
- Check Python version: `python --version` (needs 3.8+)

### Verify Installation

Run the setup verification script:
```bash
./scripts/verify-setup.sh
```

## Next Steps

1. **Single Location Analysis**:
   - Enter an ECE center name and location
   - Adjust search radius (1-6 miles)
   - Click "Analyze Competitors"

2. **Batch Analysis**:
   - Download the CSV template
   - Fill with your ECE center locations
   - Upload and analyze multiple locations at once

3. **Export Results**:
   - Download detailed CSV reports
   - View interactive maps and charts
   - Get strategic competitor insights

## Need Help?

- Check the [README](README.md) for feature documentation
- Review [CLAUDE.md](CLAUDE.md) for technical details
- Report issues on [GitHub](https://github.com/tsc-admin2025/ece-tool/issues)
