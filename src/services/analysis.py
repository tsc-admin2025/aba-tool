"""Business analysis service for ABA competitor data."""

import logging
from typing import Any, Dict, List

from src.config import IN_HOME_KEYWORDS
from src.models import AnalysisResult, Competitor, Location, SearchParameters, ServiceType

logger = logging.getLogger(__name__)


class CompetitorAnalysisService:
    """Service for analyzing competitor data."""

    def detect_service_type(self, name: str, types: List[str]) -> ServiceType:
        """Detect whether a competitor is center-based, in-home, or both.

        Uses business name keywords and Google Places type data to infer
        the service delivery model.

        Args:
        ----
            name: Business name
            types: Google Places type tags

        Returns:
        -------
            ServiceType enum value

        """
        name_lower = name.lower()

        has_in_home_signal = any(kw in name_lower for kw in IN_HOME_KEYWORDS)
        has_physical_signal = any(
            t in types
            for t in [
                "establishment",
                "health",
                "doctor",
                "physiotherapist",
                "point_of_interest",
            ]
        )

        if has_in_home_signal and has_physical_signal:
            return ServiceType.BOTH
        elif has_in_home_signal:
            return ServiceType.IN_HOME
        elif has_physical_signal:
            return ServiceType.CENTER_BASED

        return ServiceType.UNKNOWN

    def analyze_competitors(
        self,
        raw_competitors: List[Dict[str, Any]],
        search_params: SearchParameters,
        client_location: Location,
    ) -> AnalysisResult:
        """Analyze competitor data and create structured results.

        Builds a flat competitor list sorted by distance (closest first),
        then by rating (highest first). Auto-detects service type for each.

        Args:
        ----
            raw_competitors: Raw competitor data from search
            search_params: Original search parameters
            client_location: Geocoded client location

        Returns:
        -------
            AnalysisResult with analyzed competitors

        """
        competitors = []

        for comp_data in raw_competitors:
            service_type = self.detect_service_type(
                comp_data["name"], comp_data.get("types", [])
            )

            competitor = Competitor(
                name=comp_data["name"],
                place_id=comp_data["place_id"],
                location=Location(
                    lat=comp_data["lat"],
                    lng=comp_data["lng"],
                    formatted_address=comp_data.get("vicinity", ""),
                ),
                rating=comp_data.get("rating"),
                user_ratings_total=comp_data.get("user_ratings_total", 0),
                vicinity=comp_data.get("vicinity", ""),
                search_term=comp_data["search_term"],
                types=comp_data.get("types", []),
                service_type=service_type,
                distance_miles=comp_data.get("distance_miles"),
                drive_time_minutes=comp_data.get("drive_time_minutes"),
                zip_code=comp_data.get("zip_code"),
                website=comp_data.get("website"),
                phone_number=comp_data.get("phone_number"),
                operating_hours=comp_data.get("operating_hours"),
                google_maps_url=comp_data.get("google_maps_url"),
            )
            competitors.append(competitor)

        # Sort by distance (closest first), then by rating (highest first)
        competitors.sort(
            key=lambda c: (
                c.distance_miles if c.distance_miles is not None else float("inf"),
                -(c.rating or 0),
            )
        )

        logger.info(f"Analyzed {len(competitors)} competitors")

        return AnalysisResult(
            search_params=search_params,
            client_location=client_location,
            competitors=competitors,
        )
