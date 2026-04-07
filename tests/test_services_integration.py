"""Integration tests for various services."""

from unittest.mock import Mock

import pytest

from src.models import Location, ServiceType
from src.services.analysis import CompetitorAnalysisService
from src.services.geocoding import GeocodingService


class TestGeocodingService:
    """Test geocoding service functionality."""

    @pytest.fixture
    def mock_gmaps_client(self):
        """Create mock Google Maps client."""
        return Mock()

    @pytest.fixture
    def geocoding_service(self, mock_gmaps_client):
        """Create geocoding service with mocked client."""
        service = GeocodingService(mock_gmaps_client)
        return service

    def test_geocode_success(self, geocoding_service, mock_gmaps_client):
        """Test successful geocoding."""
        mock_gmaps_client.geocode.return_value = [
            {
                "geometry": {"location": {"lat": 33.9503832, "lng": -84.41384149999999}},
                "formatted_address": "100 N Charles St, Baltimore, MD 21201, USA",
            }
        ]

        result = geocoding_service.geocode_address("100 N Charles St, Baltimore, MD 21201")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["geometry"]["location"]["lat"] == 33.9503832

    def test_geocode_not_found(self, geocoding_service, mock_gmaps_client):
        """Test geocoding when address not found."""
        mock_gmaps_client.geocode.return_value = []

        result = geocoding_service.geocode_address("Invalid Address")

        assert isinstance(result, list)
        assert len(result) == 0

    def test_geocode_error(self, geocoding_service, mock_gmaps_client):
        """Test geocoding error handling."""
        mock_gmaps_client.geocode.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            geocoding_service.geocode_address("Test Address")


class TestCompetitorAnalysisService:
    """Test competitor analysis service."""

    @pytest.fixture
    def analysis_service(self):
        """Create analysis service instance."""
        return CompetitorAnalysisService()

    @pytest.fixture
    def sample_competitors(self):
        """Create sample competitor data."""
        return [
            {
                "name": "In-Home ABA Therapy Services",
                "place_id": "test1",
                "lat": 33.95,
                "lng": -84.41,
                "rating": 4.5,
                "user_ratings_total": 50,
                "vicinity": "123 Main St",
                "types": ["health", "establishment"],
                "search_term": "ABA therapy",
                "distance_miles": 1.2,
            },
            {
                "name": "Generic Behavior Clinic",
                "place_id": "test2",
                "lat": 33.96,
                "lng": -84.42,
                "rating": 3.8,
                "user_ratings_total": 20,
                "vicinity": "456 Oak St",
                "types": ["doctor", "establishment"],
                "search_term": "behavioral health clinic",
                "distance_miles": 2.5,
            },
        ]

    def test_analyze_competitors(self, analysis_service, sample_competitors):
        """Test competitor analysis with service type detection."""
        from src.models import SearchParameters

        search_params = SearchParameters(
            location_name="Test Location",
            city="Baltimore",
            state="MD",
            radius_miles=3,
        )
        client_location = Location(
            lat=33.95, lng=-84.41, formatted_address="Test Address"
        )

        result = analysis_service.analyze_competitors(
            sample_competitors, search_params, client_location
        )

        assert result.total_competitors == 2
        assert len(result.competitors) == 2

        # First competitor has "In-Home" in name + physical types = BOTH
        assert result.competitors[0].name == "In-Home ABA Therapy Services"
        assert result.competitors[0].service_type == ServiceType.BOTH

        # Second competitor has physical types but no in-home keywords = CENTER_BASED
        assert result.competitors[1].name == "Generic Behavior Clinic"
        assert result.competitors[1].service_type == ServiceType.CENTER_BASED

        # Sorted by distance (closest first)
        assert result.competitors[0].distance_miles == 1.2
        assert result.competitors[1].distance_miles == 2.5

    def test_detect_service_type(self, analysis_service):
        """Test service type detection from name and types."""
        # In-home keyword + physical types = BOTH
        st = analysis_service.detect_service_type(
            "In-Home ABA Center", ["establishment", "health"]
        )
        assert st == ServiceType.BOTH

        # In-home keyword, no physical types = IN_HOME
        st = analysis_service.detect_service_type("Mobile ABA Services", [])
        assert st == ServiceType.IN_HOME

        # Physical types, no in-home keyword = CENTER_BASED
        st = analysis_service.detect_service_type(
            "Behavior Solutions", ["health", "doctor"]
        )
        assert st == ServiceType.CENTER_BASED

        # No signals at all = UNKNOWN
        st = analysis_service.detect_service_type("Some Clinic", [])
        assert st == ServiceType.UNKNOWN
