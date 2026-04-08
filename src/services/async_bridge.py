"""Bridge service to run async competitor search in Streamlit synchronous context."""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from src.models import Location
from src.services.async_competitor_search import AsyncCompetitorSearchService

logger = logging.getLogger(__name__)


class AsyncBridgeService:
    """Bridge service to run async competitor search in synchronous Streamlit context.

    Provides a synchronous interface that internally uses async operations
    for maximum performance while maintaining compatibility with Streamlit.
    """

    def __init__(self, api_key: str):
        """Initialize with Google Maps API key."""
        self.async_service = AsyncCompetitorSearchService(api_key)
        logger.info("Async bridge service initialized")

    def search_and_enhance_competitors(
        self,
        location: Location,
        radius_miles: int,
        search_terms: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """Run complete async competitor search workflow synchronously."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    self.async_service.search_and_enhance_competitors(
                        location, radius_miles, search_terms, progress_callback
                    )
                )
                return result
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"Error in async bridge service: {e}")
            return []

    def search_competitors(
        self,
        location: Location,
        radius_miles: int,
        search_terms: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for competitors using async implementation (sync interface)."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    self.async_service.search_competitors(
                        location, radius_miles, search_terms, progress_callback
                    )
                )
                return result
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"Error in async competitor search: {e}")
            return []

    def calculate_distances(
        self, competitors: List[Dict[str, Any]], client_location: Location
    ) -> List[Dict[str, Any]]:
        """Calculate distances using async implementation (sync interface)."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    self.async_service.calculate_distances_async(competitors, client_location)
                )
                return result
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"Error in async distance calculation: {e}")
            for comp in competitors:
                comp["distance_miles"] = None
                comp["drive_time_minutes"] = None
            return competitors

    def enhance_with_place_details(
        self, competitors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enhance competitors with place details using async implementation (sync interface)."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    self.async_service.enhance_with_place_details_async(competitors)
                )
                return result
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"Error in async place details enhancement: {e}")
            for comp in competitors:
                comp["website"] = None
                comp["phone_number"] = None
                comp["operating_hours"] = None
                comp["google_maps_url"] = None
                comp["zip_code"] = None
            return competitors
