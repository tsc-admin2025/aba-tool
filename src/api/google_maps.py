"""Google Maps API client wrapper."""

import logging
from typing import Any, Dict, List, Optional

import googlemaps
import requests
from googlemaps import exceptions as gmaps_exceptions

from src.models import GeocodeResult, GeocodeStatus, Location

logger = logging.getLogger(__name__)


class GoogleMapsClient:
    """Wrapper for Google Maps API client."""

    def __init__(self, api_key: str):
        """Initialize Google Maps client."""
        if not api_key:
            raise ValueError("Google Maps API key is required")

        try:
            self.client = googlemaps.Client(key=api_key)
            logger.info("Google Maps client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Maps client: {e}")
            raise

    def geocode(self, address: str) -> GeocodeResult:
        """Geocode an address to coordinates.

        Args:
        ----
            address: Address string to geocode

        Returns:
        -------
            GeocodeResult with status and location if successful

        """
        try:
            logger.debug(f"Geocoding address: {address}")
            results = self.client.geocode(address)

            if not results:
                logger.warning(f"No geocoding results for: {address}")
                return GeocodeResult(status=GeocodeStatus.NOT_FOUND)

            # Extract location from first result
            location_data = results[0]["geometry"]["location"]
            location = Location(
                lat=location_data["lat"],
                lng=location_data["lng"],
                formatted_address=results[0]["formatted_address"],
            )

            logger.info(f"Successfully geocoded: {address} -> {location.formatted_address}")
            return GeocodeResult(status=GeocodeStatus.SUCCESS, location=location)

        except gmaps_exceptions.ApiError as e:
            logger.error(f"Google Maps API error: {e}")
            return GeocodeResult(status=GeocodeStatus.ERROR, error=f"API Error: {e!s}")
        except Exception as e:
            logger.error(f"Unexpected error during geocoding: {e}")
            return GeocodeResult(status=GeocodeStatus.ERROR, error=f"Unexpected error: {e!s}")

    def search_nearby_places(
        self,
        location: Location,
        keyword: str,
        radius: int,
        place_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search for places near a location.

        Args:
        ----
            location: Center location for search
            keyword: Keyword to search for
            radius: Search radius in meters
            place_type: Optional type filter (e.g., "school", "health"). None = no type filter.

        Returns:
        -------
            List of place results

        """
        try:
            logger.debug(f"Searching for '{keyword}' near {location.lat}, {location.lng}")

            search_kwargs: Dict[str, Any] = {
                "location": (location.lat, location.lng),
                "radius": radius,
                "keyword": keyword,
            }
            if place_type:
                search_kwargs["type"] = place_type

            results = self.client.places_nearby(**search_kwargs)

            places = results.get("results", [])
            logger.info(f"Found {len(places)} places for '{keyword}'")

            return list(places)

        except gmaps_exceptions.ApiError as e:
            logger.error(f"Google Maps API error during place search: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during place search: {e}")
            return []

    def calculate_routes_matrix(
        self, origin: Location, destinations: List[Location], units: str = "imperial"
    ) -> Optional[List[Dict[str, Any]]]:
        """Calculate distances and travel times using the new Routes API.

        Args:
        ----
            origin: Single origin location (ECE center)
            destinations: List of destination locations (competitors)
            units: 'imperial' for miles or 'metric' for kilometers

        Returns:
        -------
            List of route results or None if error

        """
        try:
            logger.debug(
                f"Calculating routes from origin to {len(destinations)} destinations using Routes API"
            )

            results = []
            for i, destination in enumerate(destinations):
                try:
                    # Use Routes API v2
                    url = "https://routes.googleapis.com/directions/v2:computeRoutes"

                    headers = {
                        "Content-Type": "application/json",
                        "X-Goog-Api-Key": self.client.key,
                        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters",
                    }

                    # Set unit preference
                    unit_system = "IMPERIAL" if units == "imperial" else "METRIC"

                    payload = {
                        "origin": {
                            "location": {
                                "latLng": {"latitude": origin.lat, "longitude": origin.lng}
                            }
                        },
                        "destination": {
                            "location": {
                                "latLng": {
                                    "latitude": destination.lat,
                                    "longitude": destination.lng,
                                }
                            }
                        },
                        "travelMode": "DRIVE",
                        "computeAlternativeRoutes": False,
                        "units": unit_system,
                    }

                    response = requests.post(url, json=payload, headers=headers)

                    if response.status_code == 200:
                        data = response.json()
                        if "routes" in data and len(data["routes"]) > 0:
                            route = data["routes"][0]

                            # Extract distance and duration
                            distance_meters = route.get("distanceMeters", 0)
                            duration = route.get("duration", "0s")

                            # Convert distance to miles or km
                            if units == "imperial":
                                distance_value = distance_meters * 0.000621371  # meters to miles
                                distance_text = f"{distance_value:.1f} mi"
                            else:
                                distance_value = distance_meters / 1000  # meters to km
                                distance_text = f"{distance_value:.1f} km"

                            # Parse duration (e.g., "123s" -> "2 mins")
                            try:
                                if isinstance(duration, str) and duration.endswith("s"):
                                    duration_seconds = int(duration.replace("s", ""))
                                elif isinstance(duration, (int, float)):
                                    duration_seconds = int(duration)
                                else:
                                    logger.warning(
                                        f"Unexpected duration format: {duration} (type: {type(duration)})"
                                    )
                                    duration_seconds = 0
                            except (ValueError, TypeError) as e:
                                logger.error(f"Error parsing duration '{duration}': {e}")
                                duration_seconds = 0
                            if duration_seconds < 60:
                                duration_text = f"{duration_seconds} sec"
                            else:
                                duration_minutes = duration_seconds // 60
                                duration_text = f"{duration_minutes} min"

                            results.append(
                                {
                                    "status": "OK",
                                    "distance": {"text": distance_text, "value": distance_value},
                                    "duration": {"text": duration_text, "value": duration_seconds},
                                }
                            )
                        else:
                            results.append({"status": "NO_ROUTE"})
                    else:
                        logger.warning(
                            f"Routes API request failed with status {response.status_code}: {response.text}"
                        )
                        results.append({"status": "API_ERROR"})

                    # Rate limiting - be gentle with the API
                    if i < len(destinations) - 1:  # Don't sleep after the last request
                        import time

                        time.sleep(0.1)

                except Exception as route_error:
                    logger.error(f"Error calculating route {i}: {route_error}")
                    results.append({"status": "ERROR"})

            logger.info(f"Calculated {len(results)} routes using Routes API")
            return results

        except Exception as e:
            logger.error(f"Unexpected error in Routes API calculation: {e}")
            return None

    def get_place_details(
        self, place_id: str, fields: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific place using Google Places Details API.

        Args:
        ----
            place_id: Google Places ID
            fields: List of fields to retrieve (e.g., ['website', 'formatted_phone_number'])

        Returns:
        -------
            Dictionary with place details or None if error

        """
        try:
            logger.debug(f"Getting place details for place_id: {place_id}")

            # Default fields if none specified
            if fields is None:
                fields = ["website", "formatted_phone_number", "opening_hours", "url"]

            result = self.client.place(place_id=place_id, fields=fields)

            if result and "result" in result:
                place_details = result["result"]
                logger.debug(
                    f"Retrieved place details for {place_id}: {list(place_details.keys())}"
                )
                return dict(place_details)
            else:
                logger.warning(f"No place details found for place_id: {place_id}")
                return None

        except gmaps_exceptions.ApiError as e:
            logger.error(f"Google Places API error for place_id {place_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting place details for {place_id}: {e}")
            return None
