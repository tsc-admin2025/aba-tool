"""Custom exceptions for ECE Tool."""


class ECEToolError(Exception):
    """Base exception for ECE Tool."""

    pass


class ConfigurationError(ECEToolError):
    """Raised when there's a configuration issue."""

    pass


class APIError(ECEToolError):
    """Raised when there's an API-related error."""

    pass


class GeocodingError(APIError):
    """Raised when geocoding fails."""

    pass


class SearchError(APIError):
    """Raised when competitor search fails."""

    pass


class ValidationError(ECEToolError):
    """Raised when data validation fails."""

    pass
