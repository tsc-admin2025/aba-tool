# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Streamlit-based competitive analysis tool for **ABA (Applied Behavior Analysis) therapy clinics** that finds nearby competitors using the Google Maps API. Adapted from the ECE Competitor Analysis Tool, with key simplifications:

- **No tier/priority system** — all competitors displayed equally, sorted by distance
- **User-editable search keywords** — defaults to ABA-specific terms, fully customizable in sidebar
- **Service type detection** — auto-detects center-based vs. in-home providers from business name/Google types, with manual override
- **No email scraping** — phone numbers from Google Places are the primary contact method

## Architecture

Modular architecture with clean separation of concerns. Pipeline: geocode → search (parallel) → distances (parallel) → place details (parallel) → service type analysis.

### Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit application, wires services + UI |
| `src/config.py` | Search keywords, in-home detection keywords, API config |
| `src/models.py` | Pydantic models: `ClientLocation`, `Competitor` (with `ServiceType`), `AnalysisResult`, `SearchParameters` |
| `src/services/analysis.py` | Service type detection + competitor analysis |
| `src/services/competitor_search.py` | Sync search service (delegates to async) |
| `src/services/async_competitor_search.py` | Async parallel search implementation |
| `src/services/async_bridge.py` | Streamlit-async compatibility layer |
| `src/services/location_csv_parser.py` | CSV parsing for batch uploads |
| `src/services/batch_validation.py` | Batch location validation |
| `src/services/geocoding.py` | Address-to-coordinates |
| `src/api/google_maps.py` | Google Maps API client |
| `src/ui/components.py` | Streamlit UI components |

### Data Flow

1. User enters location + customizes search keywords in sidebar
2. `GeocodingService` converts location to lat/lng
3. `CompetitorSearchService` runs parallel Google Maps searches for each keyword
4. Distances and place details enriched in parallel
5. `CompetitorAnalysisService` detects service type (center-based/in-home) and sorts by distance
6. Results displayed: metrics, competitor table with service type, map, analysis charts

### Models

- `ServiceType` enum: `CENTER_BASED`, `IN_HOME`, `BOTH`, `UNKNOWN`
- `Competitor.service_type`: auto-detected from business name + Google types
- `Competitor.service_type_override`: manual correction by analyst
- `Competitor.effective_service_type`: returns override if set, else auto-detected

## Running

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key
echo "GOOGLE_MAPS_API_KEY=your_key_here" > .env

# Run
streamlit run app.py
```

## Origin

Forked from `ece-tool/` (ECE Competitor Identification Tool). Changes:
- Removed tier/priority system (TARGET_COMPETITORS, TARGET_MATCHING_PATTERNS, Priority enum)
- Removed email scraping (EmailScraperService)
- Added user-editable search keywords
- Added service type auto-detection (in-home vs. center-based)
- Renamed ECECenter → ClientLocation, school_csv_parser → location_csv_parser
- Expanded US_STATES list to all 50 states
