"""Async competitor search service for parallel API calls performance improvement."""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional

import googlemaps
from googlemaps import exceptions as gmaps_exceptions

from src.config import DEFAULT_SEARCH_KEYWORDS
from src.models import Location

logger = logging.getLogger(__name__)


class AsyncCompetitorSearchService:
    """Async service for searching competitors with parallel API calls."""

    def __init__(self, api_key: str):
        """Initialize with Google Maps API key.

        Args:
        ----
            api_key: Google Maps API key

        """
        if not api_key:
            raise ValueError("Google Maps API key is required")

        self.api_key = api_key
        self.sync_client = googlemaps.Client(key=api_key)
        logger.info("Async competitor search service initialized")

    async def search_competitors(
        self,
        location: Location,
        radius_miles: int,
        search_terms: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for competitors using parallel API calls.

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
            search_terms = DEFAULT_SEARCH_KEYWORDS

        radius_meters = int(radius_miles * 1609.34)

        if progress_callback:
            progress_callback(0, len(search_terms), "Starting parallel competitor search...")

        logger.info(f"Starting parallel search for {len(search_terms)} terms")
        start_time = time.time()

        tasks = [
            self._search_single_term(location, search_term, radius_meters)
            for search_term in search_terms
        ]

        search_results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        logger.info(f"Parallel search completed in {end_time - start_time:.2f}s")

        all_competitors: List[Dict[str, Any]] = []
        successful_searches = 0

        for i, result in enumerate(search_results):
            search_term = search_terms[i]
            if isinstance(result, Exception):
                logger.error(f"Search for '{search_term}' failed: {result}")
            elif isinstance(result, list):
                all_competitors.extend(result)
                successful_searches += 1

                if progress_callback:
                    progress_callback(
                        i + 1, len(search_terms), f"Completed search for '{search_term}'"
                    )

        logger.info(f"Completed {successful_searches}/{len(search_terms)} searches")

        # Remove duplicates based on place_id
        unique_competitors = {}
        for comp in all_competitors:
            place_id = comp["place_id"]
            if place_id not in unique_competitors:
                unique_competitors[place_id] = comp

        logger.info(f"Found {len(unique_competitors)} unique competitors")
        return list(unique_competitors.values())

    async def _search_single_term(
        self, location: Location, search_term: str, radius_meters: int
    ) -> List[Dict[str, Any]]:
        """Search for a single term asynchronously using thread pool."""
        try:
            logger.debug(f"Async search for '{search_term}' near {location.lat}, {location.lng}")

            loop = asyncio.get_event_loop()
            places_result = await loop.run_in_executor(
                None, self._sync_places_search, location, search_term, radius_meters
            )

            competitors = []
            for place in places_result:
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
                competitors.append(competitor_data)

            logger.debug(f"Found {len(competitors)} competitors for '{search_term}'")
            return competitors

        except Exception as e:
            logger.error(f"Error in async search for '{search_term}': {e}")
            return []

    def _sync_places_search(
        self, location: Location, search_term: str, radius_meters: int
    ) -> List[Dict[str, Any]]:
        """Perform synchronous places search for use in thread pool."""
        try:
            results = self.sync_client.places_nearby(
                location=(location.lat, location.lng),
                radius=radius_meters,
                keyword=search_term,
            )
            return list(results.get("results", []))
        except gmaps_exceptions.ApiError as e:
            logger.error(f"Google Maps API error during place search for '{search_term}': {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during place search for '{search_term}': {e}")
            return []

    async def calculate_distances_async(
        self, competitors: List[Dict[str, Any]], client_location: Location
    ) -> List[Dict[str, Any]]:
        """Calculate distances using parallel Routes API calls.

        Args:
        ----
            competitors: List of competitor data
            client_location: Client location

        Returns:
        -------
            List of competitor data with distance_miles and drive_time_minutes added

        """
        if not competitors:
            return competitors

        logger.info(f"Starting parallel distance calculation for {len(competitors)} competitors")
        start_time = time.time()

        tasks = []
        for competitor in competitors:
            dest_location = Location(
                lat=competitor["lat"],
                lng=competitor["lng"],
                formatted_address=competitor.get("vicinity", ""),
            )
            task = self._calculate_single_route(client_location, dest_location)
            tasks.append(task)

        route_results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        logger.info(f"Parallel distance calculation completed in {end_time - start_time:.2f}s")

        enhanced_competitors = []
        for i, competitor in enumerate(competitors):
            enhanced_data = competitor.copy()

            distance_miles = None
            drive_time_minutes = None

            if i < len(route_results) and not isinstance(route_results[i], Exception):
                route_result = route_results[i]
                if isinstance(route_result, dict) and route_result.get("status") == "OK":
                    distance_info = route_result.get("distance", {})
                    distance_miles = distance_info.get("value")

                    duration_info = route_result.get("duration", {})
                    duration_seconds = duration_info.get("value")
                    if duration_seconds is not None:
                        drive_time_minutes = duration_seconds // 60
            elif isinstance(route_results[i], Exception):
                logger.error(f"Route calculation failed for competitor {i}: {route_results[i]}")

            enhanced_data["distance_miles"] = distance_miles
            enhanced_data["drive_time_minutes"] = drive_time_minutes
            enhanced_competitors.append(enhanced_data)

        logger.info(f"Enhanced {len(enhanced_competitors)} competitors with distance data")
        return enhanced_competitors

    async def _calculate_single_route(
        self, origin: Location, destination: Location
    ) -> Optional[Dict[str, Any]]:
        """Calculate a single route asynchronously using sync requests in thread pool."""
        try:
            loop = asyncio.get_event_loop()
            route_result = await loop.run_in_executor(
                None, self._sync_single_route_calculation, origin, destination
            )
            return route_result

        except Exception as e:
            logger.error(f"Error calculating single route: {e}")
            return {"status": "ERROR"}

    def _sync_single_route_calculation(
        self, origin: Location, destination: Location
    ) -> Optional[Dict[str, Any]]:
        """Calculate single route synchronously for use in thread pool."""
        try:
            import requests

            url = "https://routes.googleapis.com/directions/v2:computeRoutes"

            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": "routes.duration,routes.distanceMeters",
            }

            payload = {
                "origin": {
                    "location": {"latLng": {"latitude": origin.lat, "longitude": origin.lng}}
                },
                "destination": {
                    "location": {
                        "latLng": {"latitude": destination.lat, "longitude": destination.lng}
                    }
                },
                "travelMode": "DRIVE",
                "computeAlternativeRoutes": False,
                "units": "IMPERIAL",
            }

            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if "routes" in data and len(data["routes"]) > 0:
                    route = data["routes"][0]

                    distance_meters = route.get("distanceMeters", 0)
                    duration = route.get("duration", "0s")

                    distance_value = distance_meters * 0.000621371
                    distance_text = f"{distance_value:.1f} mi"

                    try:
                        if isinstance(duration, str) and duration.endswith("s"):
                            duration_seconds = int(duration.replace("s", ""))
                        elif isinstance(duration, (int, float)):
                            duration_seconds = int(duration)
                        else:
                            duration_seconds = 0
                    except (ValueError, TypeError):
                        duration_seconds = 0

                    if duration_seconds < 60:
                        duration_text = f"{duration_seconds} sec"
                    else:
                        duration_minutes = duration_seconds // 60
                        duration_text = f"{duration_minutes} min"

                    return {
                        "status": "OK",
                        "distance": {"text": distance_text, "value": distance_value},
                        "duration": {"text": duration_text, "value": duration_seconds},
                    }
                else:
                    return {"status": "NO_ROUTE"}
            else:
                logger.warning(f"Routes API request failed with status {response.status_code}")
                return {"status": "API_ERROR"}

        except Exception as e:
            logger.error(f"Error in sync route calculation: {e}")
            return {"status": "ERROR"}

    async def enhance_with_place_details_async(
        self, competitors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enhance competitors with place details using parallel API calls.

        Args:
        ----
            competitors: List of competitor data

        Returns:
        -------
            List of competitor data with website and other details added

        """
        if not competitors:
            return competitors

        logger.info(
            f"Starting parallel place details enhancement for {len(competitors)} competitors"
        )
        start_time = time.time()

        tasks = []
        for competitor in competitors:
            place_id = competitor.get("place_id")
            if place_id:
                task = self._get_place_details_async(place_id)
                tasks.append(task)
            else:
                tasks.append(self._create_none_task())

        details_results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        logger.info(
            f"Parallel place details enhancement completed in {end_time - start_time:.2f}s"
        )

        enhanced_competitors = []
        for i, competitor in enumerate(competitors):
            enhanced_data = competitor.copy()

            if i < len(details_results) and not isinstance(details_results[i], Exception):
                place_details = details_results[i]
                if isinstance(place_details, dict):
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
            elif isinstance(details_results[i], Exception):
                logger.error(
                    f"Place details request failed for competitor {i}: {details_results[i]}"
                )
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

    async def _create_none_task(self) -> None:
        """Create a task that returns None for competitors without place_id."""
        return None

    async def _get_place_details_async(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Get place details asynchronously using thread pool."""
        try:
            loop = asyncio.get_event_loop()
            place_details = await loop.run_in_executor(None, self._sync_place_details, place_id)
            return place_details
        except Exception as e:
            logger.error(f"Error getting async place details for {place_id}: {e}")
            return None

    def _sync_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Perform synchronous place details request for use in thread pool."""
        try:
            fields = ["website", "formatted_phone_number", "opening_hours", "url"]
            result = self.sync_client.place(place_id=place_id, fields=fields)

            if result and "result" in result:
                return dict(result["result"])
            else:
                return None

        except gmaps_exceptions.ApiError as e:
            logger.error(f"Google Places API error for place_id {place_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting place details for {place_id}: {e}")
            return None

    async def search_and_enhance_competitors(
        self,
        location: Location,
        radius_miles: int,
        search_terms: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """Complete async workflow: search, calculate distances, and enhance with details.

        Pipeline: search → distances → place details (3 steps).

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
        if progress_callback:
            progress_callback(0, 100, "Starting comprehensive competitor search...")

        # Step 1: Search for competitors (parallel by search term)
        competitors = await self.search_competitors(
            location, radius_miles, search_terms, progress_callback
        )

        if not competitors:
            return []

        if progress_callback:
            progress_callback(33, 100, "Calculating distances and drive times...")

        # Step 2: Calculate distances (parallel by competitor)
        competitors_with_distances = await self.calculate_distances_async(
            competitors, location
        )

        if progress_callback:
            progress_callback(66, 100, "Getting business details (website, phone, hours)...")

        # Step 3: Enhance with place details (parallel by competitor)
        fully_enhanced = await self.enhance_with_place_details_async(
            competitors_with_distances
        )

        if progress_callback:
            progress_callback(100, 100, "Competitor search completed!")

        return fully_enhanced
