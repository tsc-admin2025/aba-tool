"""Batch validation service for client locations."""

import logging
from difflib import SequenceMatcher
from math import asin, cos, radians, sin, sqrt
from typing import List

from src.models import (
    BatchValidationSummary,
    ClientLocation,
    GeocodeStatus,
    LocationValidationResult,
    ValidationStatus,
)
from src.services.geocoding import GeocodingService

logger = logging.getLogger(__name__)


class BatchValidationService:
    """Service for validating and geocoding multiple client locations."""

    PROXIMITY_THRESHOLD_KM = 1.0
    SIMILARITY_THRESHOLD = 0.8

    def __init__(self, geocoding_service: GeocodingService):
        self.geocoding_service = geocoding_service

    def validate_locations(
        self, locations: List[ClientLocation]
    ) -> BatchValidationSummary:
        """Validate and geocode a batch of client locations.

        Args:
        ----
            locations: List of locations to validate

        Returns:
        -------
            BatchValidationSummary with validation results

        """
        logger.info(f"Starting batch validation for {len(locations)} locations")

        results = []

        for location in locations:
            result = self._validate_single_location(location)
            results.append(result)

        self._cross_validate_locations(results)

        summary = self._categorize_results(results)

        logger.info(
            f"Batch validation complete: {summary.success_count} successful, "
            f"{summary.failed_count} failed, {summary.flagged_count} flagged"
        )

        return summary

    def _validate_single_location(
        self, location: ClientLocation
    ) -> LocationValidationResult:
        """Validate and geocode a single location."""
        logger.info(f"Validating location: {location.display_name}")

        if not location.has_sufficient_info:
            return LocationValidationResult(
                location=location,
                status=ValidationStatus.INSUFFICIENT_INFO,
                error_message="Missing address and city/state information",
            )

        try:
            if location.address:
                geocode_result = self.geocoding_service.geocode_address(location.address)
            else:
                geocode_result = self.geocoding_service.geocode_ece_location(
                    location.location_name, location.city or "", location.state or ""
                )

            if geocode_result.status == GeocodeStatus.SUCCESS:
                return LocationValidationResult(
                    location=location,
                    status=ValidationStatus.SUCCESS,
                    geocoded_location=geocode_result.location,
                )
            else:
                return LocationValidationResult(
                    location=location,
                    status=ValidationStatus.GEOCODE_FAILED,
                    error_message=geocode_result.error or "Geocoding failed",
                )

        except Exception as e:
            logger.error(f"Error validating location {location.display_name}: {e}")
            return LocationValidationResult(
                location=location, status=ValidationStatus.ERROR, error_message=str(e)
            )

    def _cross_validate_locations(
        self, results: List[LocationValidationResult]
    ) -> None:
        """Cross-validate locations for duplicates and proximity issues."""
        successful_results = [r for r in results if r.status == ValidationStatus.SUCCESS]

        for i, result1 in enumerate(successful_results):
            for _, result2 in enumerate(successful_results[i + 1 :], i + 1):
                self._check_location_pair(result1, result2)

    def _check_location_pair(
        self, result1: LocationValidationResult, result2: LocationValidationResult
    ) -> None:
        """Check a pair of locations for similarity and proximity issues."""
        loc1, loc2 = result1.location, result2.location

        name_similarity = SequenceMatcher(
            None, loc1.location_name.lower(), loc2.location_name.lower()
        ).ratio()

        if name_similarity >= self.SIMILARITY_THRESHOLD:
            warning_msg = (
                f"Similar to '{loc2.location_name}' (similarity: {name_similarity:.2f})"
            )
            result1.warnings.append(warning_msg)
            result1.similar_locations.append(loc2.location_name)

            warning_msg = (
                f"Similar to '{loc1.location_name}' (similarity: {name_similarity:.2f})"
            )
            result2.warnings.append(warning_msg)
            result2.similar_locations.append(loc1.location_name)

            if name_similarity > 0.95:
                result1.status = ValidationStatus.SIMILAR
                result2.status = ValidationStatus.SIMILAR

        if result1.geocoded_location and result2.geocoded_location:
            distance_km = self._calculate_distance(
                result1.geocoded_location.lat,
                result1.geocoded_location.lng,
                result2.geocoded_location.lat,
                result2.geocoded_location.lng,
            )

            if distance_km <= self.PROXIMITY_THRESHOLD_KM:
                warning_msg = (
                    f"Very close to '{loc2.location_name}' ({distance_km:.2f}km away)"
                )
                result1.warnings.append(warning_msg)

                warning_msg = (
                    f"Very close to '{loc1.location_name}' ({distance_km:.2f}km away)"
                )
                result2.warnings.append(warning_msg)

                if distance_km < 0.1:
                    result1.status = ValidationStatus.DUPLICATE
                    result2.status = ValidationStatus.DUPLICATE

    def _calculate_distance(
        self, lat1: float, lng1: float, lat2: float, lng2: float
    ) -> float:
        """Calculate the great circle distance between two points in kilometers."""
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])

        dlon = lng2 - lng1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))

        r = 6371
        return c * r

    def _categorize_results(
        self, results: List[LocationValidationResult]
    ) -> BatchValidationSummary:
        """Categorize validation results into successful, failed, and flagged."""
        successful = []
        failed = []
        flagged = []

        for result in results:
            if result.status == ValidationStatus.SUCCESS:
                if result.warnings:
                    flagged.append(result)
                else:
                    successful.append(result)
            elif result.status in [ValidationStatus.SIMILAR, ValidationStatus.DUPLICATE]:
                flagged.append(result)
            else:
                failed.append(result)

        return BatchValidationSummary(
            total_locations=len(results),
            successful=successful,
            failed=failed,
            flagged=flagged,
        )

    def get_validation_summary_text(self, summary: BatchValidationSummary) -> str:
        """Generate human-readable validation summary."""
        lines = [
            f"**Validation Summary for {summary.total_locations} locations:**",
            f"  {summary.success_count} Successful - Ready for analysis",
            f"  {summary.failed_count} Failed - Cannot proceed",
            f"  {summary.flagged_count} Flagged - Require review",
            "",
        ]

        if summary.failed:
            lines.append("**Failed Locations:**")
            for result in summary.failed:
                lines.append(
                    f"- {result.location.display_name} "
                    f"(Row {result.location.row_number}): {result.error_message}"
                )
            lines.append("")

        if summary.flagged:
            lines.append("**Flagged Locations:**")
            for result in summary.flagged:
                lines.append(
                    f"- {result.location.display_name} "
                    f"(Row {result.location.row_number}):"
                )
                for warning in result.warnings:
                    lines.append(f"  - {warning}")
            lines.append("")

        return "\n".join(lines)
