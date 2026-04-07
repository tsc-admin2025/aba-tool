# ABA Competitor Analysis Tool

A Streamlit-based competitive analysis tool for ABA (Applied Behavior Analysis) therapy clinics. Finds nearby competitors using the Google Maps API, with auto-detection of center-based vs. in-home service delivery models.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.24+-red.svg)
![Docker](https://img.shields.io/badge/docker-ready-green.svg)

## Features

- **Single Location Analysis**: Find ABA competitors around any location
- **Batch Analysis**: Process multiple locations via CSV upload
- **Editable Search Keywords**: Customize search terms (defaults: ABA therapy, applied behavior analysis, etc.)
- **Service Type Detection**: Auto-classifies competitors as Center-Based, In-Home, Both, or Unknown
- **Comprehensive Data Collection**:
  - Distance and drive time calculations
  - Business details (phone, website, hours)
  - Ratings and review counts
  - Google Maps links
- **Interactive Map + Charts**: Plotly visualizations with Tuscany Strategy branding
- **CSV Export**: Download full results for all competitors

## Quick Start

### Option 1: Streamlit Community Cloud (Recommended)

The app is deployed and accessible via browser — no install needed.

### Option 2: Run Locally

```bash
git clone https://github.com/tsc-admin2025/aba-tool.git
cd aba-tool
cp .env.example .env
# Edit .env and add your Google Maps API key

pip install -r requirements.txt
streamlit run app.py
```

### Option 3: Docker

```bash
docker-compose up
# Open http://localhost:8501
```

## Google Maps API Setup

Requires a Google Maps API key with these APIs enabled:
- **Geocoding API**: Convert addresses to coordinates
- **Places API**: Find nearby competitors
- **Routes API**: Calculate distances and drive times

## Usage

### Single Location
1. Enter a location name, city, and state in the sidebar
2. Edit search keywords if needed (or use defaults)
3. Set search radius (1-6 miles)
4. Click "Analyze Competitors"
5. Explore: competitor table, map, analysis charts
6. Download results as CSV

### Batch Analysis
1. Download the CSV template
2. Fill in your locations
3. Upload the CSV
4. Set search radius and keywords
5. Click "Analyze All Locations"
6. Download combined results

## Service Type Detection

The tool auto-detects how each competitor delivers services:

| Type | How Detected |
|------|-------------|
| **Center-Based** | Has physical establishment on Google Maps |
| **In-Home** | Name contains "in-home", "mobile", "telehealth", etc. |
| **Both** | Has in-home keywords AND physical location |
| **Unknown** | No clear signals — analyst can override manually |

## Development

```bash
pip install -r requirements.txt
pytest  # Run tests (17 tests)
```

## Professional Services

Developed by [Tuscany Strategy](https://tuscanystrategy.com)
