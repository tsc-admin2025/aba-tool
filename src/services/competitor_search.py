"""Competitor search service with async support."""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from src.api.google_maps import GoogleMapsClient
from src.models import Location

logger = logging.getLogger(__name__)


class CompetitorSearchService:
    """Service for searching competitors near a location with optional async support."""

    def __init__(self, google_maps_client: GoogleMapsClient, use_async: bool = True):
        """Initialize with Google Maps client.

        Args:
        ----
            google_maps_client: Google Maps client instance
            use_async: Whether to use async implementation for better performance

        """
        self.gmaps = google_maps_client
        self.use_async = use_async

        # Initialize async service if enabled
        if self.use_async:
            try:
                from src.services.async_bridge import AsyncBridgeService

                self.async_service = AsyncBridgeService(google_maps_client.client.key)
                logger.info("Async competitor search enabled for improved performance")
            except Exception as e:
                logger.warning(f"Failed to initialize async service, falling back to sync: {e}")
                self.use_async = False

    def search_competitors(
        self,
        location: Location,
        radius_miles: int,
        search_terms: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for competitors around a location.

        Args:
        ----
            location: Center location for search
            radius_miles: Search radius in miles
            search_terms: List of search keywords to use
            progress_callback: Optional callback for progress updates

        Returns:
        -------
            List of raw competitor data

        """
        if not search_terms:
            from src.config import DEFAULT_SEARCH_KEYWORDS

            search_terms = DEFAULT_SEARCH_KEYWORDS

        # Use async implementation if enabled for better performance
        if self.use_async and hasattr(self, "async_service"):
            logger.debug("Using async competitor search for improved performance")
            return self.async_service.search_competitors(
                location, radius_miles, search_terms, progress_callback
            )

        # Fallback to synchronous implementation
        logger.debug("Using synchronous competitor search")
        radius_meters = int(radius_miles * 1609.34)  # Convert miles to meters
        all_competitors = []

        for i, search_term in enumerate(search_terms):
            logger.info(f"Searching for '{search_term}' near {location.lat}, {location.lng}")

            if progress_callback:
                progress_callback(i + 1, len(search_terms), f"Searching for '{search_term}'...")

            try:
                places = self.gmaps.search_nearby_places(
                    location=location,
                    keyword=search_term,
                    radius=radius_meters,
                )

                for place in places:
                    competitor_data = {
                        "name": place["name"],
                        "place_id": place["place_id"],
                        "lat": place["geometry"]["location"]["lat"],
                        "lng": place["geometry"]["location"]["lng"],
                        "rating": place.get("rating"),
                        "user_ratings_total": place.get("user_ratings_total", 0),
                        "types": place.get("types", []),
                        "vicinity": place.get("vicinity", ""),
                        "search_term": search_term,
                    }
                    all_competitors.append(competitor_data)

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error searching for '{search_term}': {e}")

        # Remove duplicates based on place_id
        unique_competitors = {}
        for comp in all_competitors:
            place_id = comp["place_id"]
            if place_id not in unique_competitors:
                unique_competitors[place_id] = comp

        logger.info(f"Found {len(unique_competitors)} unique competitors")
        return list(unique_competitors.values())

    def calculate_distances(
        self, competitors: List[Dict[str, Any]], client_location: Location
    ) -> List[Dict[str, Any]]:
        """Calculate distances from client location to competitors.

        Args:
        ----
            competitors: List of competitor data
            client_location: Client location

        Returns:
        -------
            List of competitor data with distance_miles added

        """
        # Use async implementation if enabled for better performance
        if self.use_async and hasattr(self, "async_service"):
            logger.debug("Using async distance calculation for improved performance")
            return self.async_service.calculate_distances(competitors, client_location)

        # Fallback to synchronous implementation
        logger.debug("Using synchronous distance calculation")
        if not competitors:
            return competitors

        try:
            # Create competitor locations
            competitor_locations = [
                Location(
                    lat=comp["lat"], lng=comp["lng"], formatted_address=comp.get("vicinity", "")
                )
                for comp in competitors
            ]

            # Calculate routes using Routes API
            routes_results = self.gmaps.calculate_routes_matrix(
                origin=client_location, destinations=competitor_locations, units="imperial"
            )

            # Add distance data to competitors
            enhanced_competitors = []
            for i, competitor in enumerate(competitors):
                enhanced_data = competitor.copy()

                distance_miles = None
                drive_time_minutes = None
                if routes_results and i < len(routes_results):
                    route_result = routes_results[i]
                    if route_result.get("status") == "OK":
                        distance_info = route_result.get("distance", {})
                        distance_miles = distance_info.get("value")

                        duration_info = route_result.get("duration", {})
                        duration_seconds = duration_info.get("value")
                        if duration_seconds is not None:
                            drive_time_minutes = duration_seconds // 60

                enhanced_data["distance_miles"] = distance_miles
                enhanced_data["drive_time_minutes"] = drive_time_minutes
                enhanced_competitors.append(enhanced_data)

            logger.info(f"Calculated distances for {len(enhanced_competitors)} competitors")
            return enhanced_competitors

        except Exception as e:
            logger.error(f"Error calculating distances: {e}")
            for comp in competitors:
                comp["distance_miles"] = None
                comp["drive_time_minutes"] = None
            return competitors

    def enhance_with_place_details(
        self, competitors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enhance competitors with additional details from Google Places Details API.

        Args:
        ----
            competitors: List of competitor data

        Returns:
        -------
            List of competitor data with website and other details added

        """
        # Use async implementation if enabled for better performance
        if self.use_async and hasattr(self, "async_service"):
            logger.debug("Using async place details enhancement for improved performance")
            return self.async_service.enhance_with_place_details(competitors)

        # Fallback to synchronous implementation
        logger.debug("Using synchronous place details enhancement")
        if not competitors:
            return competitors

        try:
            enhanced_competitors = []

            for i, competitor in enumerate(competitors):
                enhanced_data = competitor.copy()
                place_id = competitor.get("place_id")

                if place_id:
                    if i > 0:
                        time.sleep(0.2)

                    place_details = self.gmaps.get_place_details(
                        place_id=place_id,
                        fields=[
                            "website",
                            "formatted_phone_number",
                            "opening_hours",
                            "url",
                        ],
                    )

                    if place_details:
                        website = place_details.get("website")
                        phone_number = place_details.get("formatted_phone_number")
                        google_maps_url = place_details.get("url")

                        opening_hours = place_details.get("opening_hours", {})
                        if opening_hours and "weekday_text" in opening_hours:
                            operating_hours = opening_hours["weekday_text"]
                        else:
                            operating_hours = None

                        enhanced_data["website"] = website
                        enhanced_data["phone_number"] = phone_number
                        enhanced_data["operating_hours"] = operating_hours
                        enhanced_data["google_maps_url"] = google_maps_url
                    else:
                        enhanced_data["website"] = None
                        enhanced_data["phone_number"] = None
                        enhanced_data["operating_hours"] = None
                        enhanced_data["google_maps_url"] = None
                else:
                    enhanced_data["website"] = None
                    enhanced_data["phone_number"] = None
                    enhanced_data["operating_hours"] = None
                    enhanced_data["google_maps_url"] = None

                enhanced_competitors.append(enhanced_data)

            logger.info(f"Enhanced {len(enhanced_competitors)} competitors with place details")
            return enhanced_competitors

        except Exception as e:
            logger.error(f"Error enhancing competitors with place details: {e}")
            for comp in competitors:
                comp["website"] = None
                comp["phone_number"] = None
                comp["operating_hours"] = None
                comp["google_maps_url"] = None
            return competitors

    def search_and_enhance_competitors(
        self,
        location: Location,
        radius_miles: int,
        search_terms: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """Complete competitor search workflow with all enhancements.

        Pipeline: search → distances → place details (no email scraping).

        Args:
        ----
            location: Center location for search
            radius_miles: Search radius in miles
            search_terms: List of search keywords to use
            progress_callback: Optional callback for progress updates

        Returns:
        -------
            List of fully enhanced competitor data

        """
        # Use async implementation for complete workflow if enabled
        if self.use_async and hasattr(self, "async_service"):
            logger.debug("Using async complete workflow for maximum performance")
            return self.async_service.search_and_enhance_competitors(
                location, radius_miles, search_terms, progress_callback
            )

        # Fallback to synchronous workflow
        logger.debug("Using synchronous complete workflow")

        # Step 1: Search for competitors
        if progress_callback:
            progress_callback(0, 100, "Searching for competitors...")

        competitors = self.search_competitors(location, radius_miles, search_terms)

        if not competitors:
            return []

        # Step 2: Calculate distances
        if progress_callback:
            progress_callback(33, 100, "Calculating distances and drive times...")

        competitors_with_distances = self.calculate_distances(competitors, location)

        # Step 3: Enhance with place details
        if progress_callback:
            progress_callback(66, 100, "Getting business details (website, phone, hours)...")

        fully_enhanced = self.enhance_with_place_details(competitors_with_distances)

        if progress_callback:
            progress_callback(100, 100, "Competitor search completed!")

        return fully_enhanced
