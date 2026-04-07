# ECE Competitor Identification Tool

A powerful Streamlit-based competitive analysis tool for early childhood education centers. This tool helps identify and categorize nearby competitors using the Google Maps API, providing strategic insights through interactive visualizations and comprehensive data exports.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.24+-red.svg)
![Docker](https://img.shields.io/badge/docker-ready-green.svg)
![License](https://img.shields.io/badge/license-proprietary-orange.svg)

## Features

- **Single Location Analysis**: Analyze competitors around a specific ECE center
- **Batch Analysis**: Process multiple locations via CSV upload
- **Smart Competitor Categorization**: Automatic tier classification (Tier 5/4/3)
- **Comprehensive Data Collection**:
  - Distance and drive time calculations
  - Business details (website, phone, hours)
  - Ratings and review counts
  - Google Maps integration
- **Interactive Visualizations**: Maps, charts, and analytics
- **Professional Export Options**: Detailed CSV reports

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/tsc-admin2025/ece-tool.git
cd ece-tool

# Verify setup (optional but recommended)
./scripts/verify-setup.sh

# Copy environment template and add your API key
cp .env.example .env
# Edit .env and add your Google Maps API key
# See docs/ENVIRONMENT_SETUP.md for detailed instructions
```

### 2. Choose Your Method

#### Using Docker (Recommended - No Python Required)

```bash
# Run with Docker Compose
docker-compose up
```

Visit http://localhost:8501

#### Using Python (Alternative)

```bash
# Install the package
pip install .

# Run the application
streamlit run app.py
```

Visit http://localhost:8501

## Google Maps API Setup

This tool requires a Google Maps API key with the following APIs enabled:
- **Geocoding API**: Convert addresses to coordinates
- **Places API**: Find nearby competitors
- **Routes API**: Calculate distances and drive times

**For detailed setup instructions, see [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md)**

Expected API usage: ~$200 for analyzing 400 schools

## Usage

### Single Location Analysis
1. Enter an ECE center name and address in the sidebar
2. Adjust search radius (default: 10 miles)
3. Click "Analyze Competitors"
4. Explore results across multiple tabs
5. Export data as CSV

### Batch Analysis
1. Download the CSV template
2. Fill in center locations
3. Upload the completed CSV
4. Review validation results
5. Process valid locations
6. Export comprehensive results

## Competitor Tiers

- **Tier 5**: Premium competitors (e.g., Bright Horizons, Goddard Schools)
- **Tier 4**: Mid-tier competitors (e.g., Lightbridge Academy, O2B Kids)
- **Tier 3**: Value competitors (e.g., KinderCare, La Petite Academy)

## Development

### Modern Setup

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install

# Generate secrets baseline (first time only)
detect-secrets scan > .secrets.baseline

# Run tests
pytest

# Run code quality checks
pre-commit run --all-files
```

### Project Structure

```
ece-tool/
├── app.py                    # Main Streamlit application
├── src/
│   ├── api/                  # Google Maps API integration
│   ├── services/             # Business logic services
│   ├── models.py             # Pydantic data models
│   ├── config.py             # Configuration and constants
│   └── ui/                   # Streamlit UI components
├── tests/                    # Test suite
├── pyproject.toml            # Modern Python project config
└── docker-compose.yml        # Container orchestration
```

## Professional Services

Developed by [Tuscany Strategy](https://tuscanystrategy.com)

## License

Proprietary - All rights reserved
