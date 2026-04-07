"""Tests for data models."""

from src.models import Competitor, GeocodeResult, GeocodeStatus, Location, ServiceType


def test_service_type_enum():
    """Test ServiceType enum values."""
    assert ServiceType.CENTER_BASED.value == "Center-Based"
    assert ServiceType.IN_HOME.value == "In-Home"
    assert ServiceType.BOTH.value == "Both"
    assert ServiceType.UNKNOWN.value == "Unknown"


def test_location_model():
    """Test Location model."""
    location = Location(lat=40.7128, lng=-74.0060, formatted_address="New York, NY, USA")
    assert location.lat == 40.7128
    assert location.lng == -74.0060
    assert location.formatted_address == "New York, NY, USA"


def test_competitor_model():
    """Test Competitor model."""
    location = Location(lat=40.7128, lng=-74.0060, formatted_address="Test Address")

    competitor = Competitor(
        name="Test ABA Clinic",
        place_id="test123",
        location=location,
        rating=4.5,
        user_ratings_total=100,
        service_type=ServiceType.CENTER_BASED,
        vicinity="123 Test St",
        search_term="ABA therapy",
    )

    assert competitor.effective_service_type == ServiceType.CENTER_BASED
    assert competitor.display_service_type == "Center-Based"

    # Test with manual override
    competitor.service_type_override = ServiceType.IN_HOME
    assert competitor.effective_service_type == ServiceType.IN_HOME
    assert competitor.display_service_type == "In-Home (manual)"


def test_competitor_default_service_type():
    """Test Competitor defaults to UNKNOWN service type."""
    location = Location(lat=40.7128, lng=-74.0060, formatted_address="Test Address")

    competitor = Competitor(
        name="Test Clinic",
        place_id="test456",
        location=location,
        search_term="ABA therapy",
    )

    assert competitor.effective_service_type == ServiceType.UNKNOWN
    assert competitor.display_service_type == "Unknown"


def test_geocode_result():
    """Test GeocodeResult model."""
    # Test successful result
    location = Location(lat=40.7128, lng=-74.0060, formatted_address="New York, NY, USA")
    result = GeocodeResult(status=GeocodeStatus.SUCCESS, location=location)
    assert result.status == GeocodeStatus.SUCCESS
    assert result.location == location
    assert result.error is None

    # Test error result
    error_result = GeocodeResult(status=GeocodeStatus.ERROR, error="API rate limit exceeded")
    assert error_result.status == GeocodeStatus.ERROR
    assert error_result.location is None
    assert error_result.error == "API rate limit exceeded"
