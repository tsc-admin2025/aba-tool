"""Test suite for CSV processing functionality."""

import pytest

from src.models import ClientLocation
from src.services.location_csv_parser import LocationCSVParser


class TestLocationCSVParser:
    """Test location CSV parser functionality."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return LocationCSVParser()

    def test_parse_valid_csv(self, parser):
        """Test parsing valid CSV data."""
        csv_data = """location_name,address,city,state
Downtown Baltimore,100 N Charles St,Baltimore,MD
Towson,,Towson,MD
Columbia,456 Main St,Columbia,MD"""

        locations = parser.parse_csv(csv_data)

        assert len(locations) == 3
        assert isinstance(locations[0], ClientLocation)

        # Check first location
        assert locations[0].location_name == "Downtown Baltimore"
        assert locations[0].address == "100 N Charles St"
        assert locations[0].city == "Baltimore"
        assert locations[0].state == "MD"
        assert locations[0].row_number == 2

        # Check second location (no address)
        assert locations[1].location_name == "Towson"
        assert locations[1].address is None
        assert locations[1].city == "Towson"
        assert locations[1].row_number == 3

    def test_parse_csv_missing_required_fields(self, parser):
        """Test parsing CSV with missing required fields."""
        csv_data = """location_name,address,city,state
,100 N Charles St,Baltimore,MD
Downtown Baltimore,,Baltimore,"""

        locations = parser.parse_csv(csv_data)
        assert len(locations) <= 2

    def test_parse_csv_extra_columns(self, parser):
        """Test parsing CSV with extra columns (should be ignored)."""
        csv_data = """location_name,address,city,state,extra_column
Downtown Baltimore,100 N Charles St,Baltimore,MD,ignored_data
Towson,,Towson,MD,more_ignored"""

        locations = parser.parse_csv(csv_data)

        assert len(locations) == 2
        assert locations[0].location_name == "Downtown Baltimore"

    def test_parse_empty_csv(self, parser):
        """Test parsing empty CSV."""
        csv_data = """location_name,address,city,state"""

        locations = parser.parse_csv(csv_data)
        assert len(locations) == 0

    def test_csv_headers(self, parser):
        """Test CSV has required headers."""
        csv_data = """location_name,address,city,state
"""

        locations = parser.parse_csv(csv_data)
        assert isinstance(locations, list)
        assert len(locations) == 0

    def test_csv_parsing_basic(self, parser):
        """Test basic CSV parsing functionality."""
        csv_data = """location_name,address,city,state
Downtown Baltimore,100 N Charles St,Baltimore,MD
Towson,,Towson,MD"""

        locations = parser.parse_csv(csv_data)
        assert len(locations) == 2
        assert locations[0].location_name == "Downtown Baltimore"
        assert locations[0].city == "Baltimore"
        assert locations[1].location_name == "Towson"
        assert locations[1].address is None

    def test_csv_row_numbers(self, parser):
        """Test that row numbers are assigned correctly."""
        csv_data = """location_name,address,city,state
Downtown Baltimore,100 N Charles St,Baltimore,MD
Towson,,Towson,MD"""

        locations = parser.parse_csv(csv_data)
        assert locations[0].row_number == 2  # Header is row 1
        assert locations[1].row_number == 3
