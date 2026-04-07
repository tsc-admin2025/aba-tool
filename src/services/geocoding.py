"""Geocoding service for location resolution."""

import logging

from src.api.google_maps import GoogleMapsClient
from src.models import GeocodeResult, GeocodeStatus

logger = logging.getLogger(__name__)


class GeocodingService:
    """Service for geocoding ECE center locations."""

    def __init__(self, google_maps_client: GoogleMapsClient):
        """Initialize with Google Maps client."""
        self.gmaps = google_maps_client

    def geocode_ece_location(self, location_name: str, city: str, state: str) -> GeocodeResult:
        """Geocode an ECE center location.

        Args:
        ----
            location_name: Name of the ECE center location
            city: City name
            state: State code

        Returns:
        -------
            GeocodeResult with location if successful

        """
        # Try full center name first
        full_address = f"{location_name}, {city}, {state}"
        logger.info(f"Attempting to geocode: {full_address}")

        result = self.gmaps.geocode(full_address)

        if result.status == GeocodeStatus.SUCCESS:
            return result

        # Fallback to city, state only
        fallback_address = f"{city}, {state}"
        logger.info(f"Falling back to geocode: {fallback_address}")

        return self.gmaps.geocode(fallback_address)

    def geocode_address(self, address: str) -> GeocodeResult:
        """Geocode a full address string.

        Args:
        ----
            address: Full address string

        Returns:
        -------
            GeocodeResult with location if successful

        """
        logger.info(f"Attempting to geocode address: {address}")
        return self.gmaps.geocode(address)
