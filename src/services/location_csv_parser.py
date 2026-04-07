"""CSV parsing service for client location uploads."""

import logging
from difflib import SequenceMatcher
from io import StringIO
from typing import Any, ClassVar, List, Optional

import pandas as pd

from src.exceptions import ValidationError
from src.models import ClientLocation

logger = logging.getLogger(__name__)


class LocationCSVParser:
    """Service for parsing and validating uploaded location CSV files."""

    REQUIRED_COLUMNS: ClassVar[List[str]] = ["location_name"]
    OPTIONAL_COLUMNS: ClassVar[List[str]] = ["address", "city", "state"]
    SIMILARITY_THRESHOLD = 0.8

    def parse_csv(self, csv_content: str) -> List[ClientLocation]:
        """Parse CSV content and return list of client locations.

        Args:
        ----
            csv_content: Raw CSV content as string

        Returns:
        -------
            List of ClientLocation objects

        Raises:
        ------
            ValidationError: If CSV format is invalid

        """
        try:
            df = pd.read_csv(StringIO(csv_content))
            self._validate_columns(df)
            df = self._clean_dataframe(df)

            locations = []
            for idx, row in df.iterrows():
                location = self._row_to_location(row, idx + 2)  # +2 for header and 0-indexing
                if location:
                    locations.append(location)

            self._validate_location_list(locations)

            logger.info(f"Successfully parsed {len(locations)} locations from CSV")
            return locations

        except pd.errors.EmptyDataError as e:
            raise ValidationError("CSV file is empty") from e
        except pd.errors.ParserError as e:
            raise ValidationError(f"Invalid CSV format: {e}") from e
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            raise ValidationError(f"Failed to parse CSV: {e}") from e

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Validate that required columns are present."""
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            raise ValidationError(
                f"Missing required columns: {', '.join(missing_columns)}. "
                f"Required: {', '.join(self.REQUIRED_COLUMNS)}"
            )

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize dataframe."""
        df = df.dropna(subset=["location_name"]).copy()

        string_columns = df.select_dtypes(include=["object"]).columns
        for col in string_columns:
            df[col] = df[col].str.strip()

        if "state" in df.columns:
            df["state"] = df["state"].apply(self._standardize_state)

        return df

    def _standardize_state(self, state_value: Any) -> Optional[str]:
        """Standardize state values to uppercase 2-letter codes."""
        if pd.isna(state_value):
            return None

        state_str = str(state_value).strip().upper()

        if len(state_str) == 2:
            return state_str

        state_mapping = {
            "ALABAMA": "AL",
            "ALASKA": "AK",
            "ARIZONA": "AZ",
            "ARKANSAS": "AR",
            "CALIFORNIA": "CA",
            "COLORADO": "CO",
            "CONNECTICUT": "CT",
            "DELAWARE": "DE",
            "FLORIDA": "FL",
            "GEORGIA": "GA",
            "HAWAII": "HI",
            "IDAHO": "ID",
            "ILLINOIS": "IL",
            "INDIANA": "IN",
            "IOWA": "IA",
            "KANSAS": "KS",
            "KENTUCKY": "KY",
            "LOUISIANA": "LA",
            "MAINE": "ME",
            "MARYLAND": "MD",
            "MASSACHUSETTS": "MA",
            "MICHIGAN": "MI",
            "MINNESOTA": "MN",
            "MISSISSIPPI": "MS",
            "MISSOURI": "MO",
            "MONTANA": "MT",
            "NEBRASKA": "NE",
            "NEVADA": "NV",
            "NEW HAMPSHIRE": "NH",
            "NEW JERSEY": "NJ",
            "NEW MEXICO": "NM",
            "NEW YORK": "NY",
            "NORTH CAROLINA": "NC",
            "NORTH DAKOTA": "ND",
            "OHIO": "OH",
            "OKLAHOMA": "OK",
            "OREGON": "OR",
            "PENNSYLVANIA": "PA",
            "RHODE ISLAND": "RI",
            "SOUTH CAROLINA": "SC",
            "SOUTH DAKOTA": "SD",
            "TENNESSEE": "TN",
            "TEXAS": "TX",
            "UTAH": "UT",
            "VERMONT": "VT",
            "VIRGINIA": "VA",
            "WASHINGTON": "WA",
            "WEST VIRGINIA": "WV",
            "WISCONSIN": "WI",
            "WYOMING": "WY",
        }

        return state_mapping.get(state_str, state_str)

    def _row_to_location(self, row: pd.Series, row_number: int) -> Optional[ClientLocation]:
        """Convert dataframe row to ClientLocation object."""
        try:
            location_name = row["location_name"]

            if not location_name or pd.isna(location_name):
                logger.warning(f"Skipping row {row_number} with missing location name")
                return None

            address = row.get("address", None)
            city = row.get("city", None)
            state = row.get("state", None)

            if address and pd.isna(address):
                address = None
            if city and pd.isna(city):
                city = None
            if state and pd.isna(state):
                state = None

            return ClientLocation(
                location_name=str(location_name).strip(),
                address=address.strip() if address else None,
                city=city.strip() if city else None,
                state=state,
                row_number=row_number,
            )

        except Exception as e:
            logger.warning(f"Failed to parse row {row_number}: {dict(row)}, error: {e}")
            return None

    def _validate_location_list(self, locations: List[ClientLocation]) -> None:
        """Validate list of locations for duplicates and similar names."""
        location_names = [loc.location_name.lower() for loc in locations]

        duplicates = set()
        seen = set()
        for name in location_names:
            if name in seen:
                duplicates.add(name)
            seen.add(name)

        if duplicates:
            duplicate_names = [name.title() for name in duplicates]
            logger.warning(f"Found duplicate location names: {duplicate_names}")

        similar_pairs = []
        for i, loc1 in enumerate(locations):
            for _, loc2 in enumerate(locations[i + 1 :], i + 1):
                similarity = SequenceMatcher(
                    None, loc1.location_name.lower(), loc2.location_name.lower()
                ).ratio()
                if similarity >= self.SIMILARITY_THRESHOLD:
                    similar_pairs.append((loc1.location_name, loc2.location_name, similarity))

        if similar_pairs:
            logger.warning(f"Found {len(similar_pairs)} pairs of similar location names")

    def get_csv_template(self) -> str:
        """Return a CSV template string for user reference."""
        template_data = {
            "location_name": ["Downtown Baltimore", "Towson", "Columbia"],
            "address": [
                "100 N Charles St, Baltimore, MD 21201",
                "",
                "456 Main St, Columbia, MD 21044",
            ],
            "city": ["Baltimore", "Towson", "Columbia"],
            "state": ["MD", "MD", "MD"],
        }

        df = pd.DataFrame(template_data)
        csv_content: str = df.to_csv(index=False)
        return csv_content

    def get_validation_instructions(self) -> str:
        """Return instructions for CSV format and validation."""
        return """
        **CSV Format Requirements:**

        **Required Columns:**
        - `location_name`: Name or label for the location (e.g., "Downtown Baltimore")

        **Optional Columns:**
        - `address`: Full street address (if available)
        - `city`: City name (required if address not provided)
        - `state`: State code (required if address not provided)

        **Validation Rules:**
        - Duplicate location names will be flagged
        - Similar location names (>80% similarity) will be warned about
        - Locations without sufficient location info will be flagged

        **Examples:**
        ```
        location_name,address,city,state
        Downtown Baltimore,100 N Charles St Baltimore MD 21201,Baltimore,MD
        Towson,,Towson,MD
        Columbia,456 Main St Columbia MD 21044,,
        ```
        """
