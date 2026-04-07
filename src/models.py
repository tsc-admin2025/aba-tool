"""Data models for ABA Competitor Analysis Tool."""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ServiceType(str, Enum):
    """Service delivery type for ABA providers."""

    CENTER_BASED = "Center-Based"
    IN_HOME = "In-Home"
    BOTH = "Both"
    UNKNOWN = "Unknown"


class GeocodeStatus(str, Enum):
    """Status of geocoding operation."""

    SUCCESS = "success"
    NOT_FOUND = "not_found"
    ERROR = "error"


class ValidationStatus(str, Enum):
    """Status of location validation."""

    SUCCESS = "success"
    DUPLICATE = "duplicate"
    SIMILAR = "similar"
    INSUFFICIENT_INFO = "insufficient_info"
    GEOCODE_FAILED = "geocode_failed"
    ERROR = "error"


class Location(BaseModel):
    """Geographic location model."""

    model_config = ConfigDict(strict=False)

    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    formatted_address: str = Field(..., description="Formatted address string")


class GeocodeResult(BaseModel):
    """Result of a geocoding operation."""

    status: GeocodeStatus
    location: Optional[Location] = None
    error: Optional[str] = None


class ClientLocation(BaseModel):
    """Client location model for batch analysis."""

    location_name: str = Field(..., description="Location name")
    address: Optional[str] = Field(None, description="Full address if provided")
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State code")
    row_number: int = Field(..., description="Original CSV row number for reference")

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        return f"{self.location_name}"

    @property
    def has_sufficient_info(self) -> bool:
        """Check if location has enough info for geocoding."""
        return bool(self.address or (self.city and self.state))


class LocationValidationResult(BaseModel):
    """Result of location validation and geocoding."""

    location: ClientLocation
    status: ValidationStatus
    geocoded_location: Optional[Location] = None
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    similar_locations: List[str] = Field(
        default_factory=list, description="Names of similar locations found"
    )

    @property
    def is_valid(self) -> bool:
        """Check if location validation was successful."""
        return self.status == ValidationStatus.SUCCESS


class BatchValidationSummary(BaseModel):
    """Summary of batch location validation results."""

    total_locations: int
    successful: List[LocationValidationResult] = Field(default_factory=list)
    failed: List[LocationValidationResult] = Field(default_factory=list)
    flagged: List[LocationValidationResult] = Field(default_factory=list)

    @property
    def success_count(self) -> int:
        return len(self.successful)

    @property
    def failed_count(self) -> int:
        return len(self.failed)

    @property
    def flagged_count(self) -> int:
        return len(self.flagged)


class Competitor(BaseModel):
    """Competitor business model."""

    model_config = ConfigDict(strict=False)

    name: str = Field(..., description="Business name")
    place_id: str = Field(..., description="Google Places ID")
    location: Location = Field(..., description="Geographic location")
    rating: Optional[float] = Field(None, description="Google rating")
    user_ratings_total: int = Field(0, ge=0, description="Total number of ratings")
    vicinity: str = Field("", description="Address vicinity")
    search_term: str = Field(..., description="Search term that found this competitor")
    types: List[str] = Field(default_factory=list, description="Google Places types")

    @field_validator("rating", mode="before")
    @classmethod
    def coerce_rating(cls, v):
        if v is None:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    @field_validator("user_ratings_total", mode="before")
    @classmethod
    def coerce_ratings_total(cls, v):
        if v is None:
            return 0
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0

    @field_validator("vicinity", mode="before")
    @classmethod
    def coerce_vicinity(cls, v):
        return str(v) if v is not None else ""

    @field_validator("drive_time_minutes", mode="before")
    @classmethod
    def coerce_drive_time(cls, v):
        if v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    # Service type classification
    service_type: ServiceType = Field(
        ServiceType.UNKNOWN, description="Auto-detected service delivery type"
    )
    service_type_override: Optional[ServiceType] = Field(
        None, description="Manual override for service type"
    )

    # Distance and time calculation fields
    distance_miles: Optional[float] = Field(
        None, description="Distance from client location in miles"
    )
    drive_time_minutes: Optional[int] = Field(
        None, description="Drive time from client location in minutes"
    )

    # Additional business information from Places Details API
    website: Optional[str] = Field(None, description="Competitor website URL")
    phone_number: Optional[str] = Field(None, description="Competitor phone number")
    operating_hours: Optional[List[str]] = Field(None, description="Competitor operating hours")
    google_maps_url: Optional[str] = Field(None, description="Google Maps URL for competitor")

    @property
    def effective_service_type(self) -> ServiceType:
        """Return manual override if set, otherwise auto-detected type."""
        if self.service_type_override is not None:
            return self.service_type_override
        return self.service_type

    @property
    def display_service_type(self) -> str:
        """Display service type with override indicator."""
        st = self.effective_service_type
        if self.service_type_override is not None:
            return f"{st.value} (manual)"
        return st.value

    @property
    def display_distance(self) -> str:
        """Display distance in miles or fallback."""
        if self.distance_miles is not None:
            return f"{self.distance_miles:.1f} mi"
        return "N/A"

    @property
    def display_drive_time(self) -> str:
        """Display drive time in minutes or fallback."""
        if self.drive_time_minutes is not None:
            if self.drive_time_minutes == 0:
                return "< 1 min"
            return f"{self.drive_time_minutes} min"
        return "N/A"

    @property
    def display_website(self) -> str:
        """Display website URL or fallback."""
        if self.website:
            return self.website
        return "N/A"

    @property
    def display_phone_number(self) -> str:
        """Display phone number or fallback."""
        if self.phone_number:
            return self.phone_number
        return "N/A"

    @property
    def display_operating_hours(self) -> str:
        """Display operating hours or fallback."""
        if self.operating_hours:
            return "; ".join(self.operating_hours)
        return "N/A"

    @property
    def display_google_maps_url(self) -> str:
        """Display Google Maps URL or fallback."""
        if self.google_maps_url:
            return self.google_maps_url
        return "N/A"


class SearchParameters(BaseModel):
    """Parameters for competitor search."""

    location_name: str = Field(..., description="Client location name")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State code")
    radius_miles: int = Field(2, ge=1, le=6, description="Search radius in miles")
    search_keywords: List[str] = Field(
        default_factory=list, description="Search keywords for finding competitors"
    )


class AnalysisResult(BaseModel):
    """Complete analysis result for a location."""

    model_config = ConfigDict(strict=False)

    client_location: Location
    search_params: SearchParameters
    competitors: List[Competitor]

    @property
    def total_competitors(self) -> int:
        """Total number of competitors found."""
        return len(self.competitors)

    @property
    def average_rating(self) -> Optional[float]:
        """Average rating of all competitors with ratings."""
        ratings = [c.rating for c in self.competitors if c.rating is not None]
        return sum(ratings) / len(ratings) if ratings else None

    @property
    def center_based_count(self) -> int:
        """Count of center-based competitors."""
        return len(
            [c for c in self.competitors if c.effective_service_type == ServiceType.CENTER_BASED]
        )

    @property
    def in_home_count(self) -> int:
        """Count of in-home competitors."""
        return len(
            [c for c in self.competitors if c.effective_service_type == ServiceType.IN_HOME]
        )

    @property
    def closest_competitor(self) -> Optional[Competitor]:
        """Get the closest competitor by distance."""
        with_distance = [c for c in self.competitors if c.distance_miles is not None]
        if with_distance:
            return min(with_distance, key=lambda c: c.distance_miles)  # type: ignore[arg-type,return-value]
        return None


class MultiLocationAnalysis(BaseModel):
    """Analysis results for multiple client locations."""

    validation_summary: BatchValidationSummary
    location_results: Dict[str, AnalysisResult] = Field(default_factory=dict)

    @property
    def total_locations_analyzed(self) -> int:
        """Total number of locations successfully analyzed."""
        return len(self.location_results)

    @property
    def total_competitors_found(self) -> int:
        """Total competitors across all locations."""
        return sum(len(result.competitors) for result in self.location_results.values())
