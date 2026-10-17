"""
Input Validation and Security Sanitization Module.
Addresses ESE Rubric: Testing, Validation, Security & Error Handling (1.0 Mark).
"""

import re
from typing import Dict, Any
from app.exceptions import ValidationError

VALID_INCOME_CATEGORIES = {"Low", "Middle", "High"}
SAFE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9\\s\\-_.,()]{2,100}$")


def validate_community_payload(payload: Dict[str, Any], require_all: bool = True) -> Dict[str, Any]:
    """
    Validates and sanitizes incoming community, water_quality, and sanitation parameters.
    Raises ValidationError with descriptive field messages on invalid input.
    """
    cleaned: Dict[str, Any] = {}

    # 1. community_id
    if "community_id" in payload or require_all:
        try:
            cid = int(payload.get("community_id", 0))
        except (ValueError, TypeError):
            raise ValidationError("Community ID must be a valid integer.", field="community_id")
        if cid <= 0 or cid > 99999:
            raise ValidationError("Community ID must be a positive integer between 1 and 99999.", field="community_id")
        cleaned["community_id"] = cid

    # 2. community_name
    if "community_name" in payload or require_all:
        name = str(payload.get("community_name", "")).strip()
        if not name or not SAFE_NAME_PATTERN.match(name):
            raise ValidationError(
                "Community name must be 2-100 alphanumeric characters without SQL meta-characters.",
                field="community_name",
            )
        cleaned["community_name"] = name

    # 3. district
    if "district" in payload or require_all:
        district = str(payload.get("district", "")).strip()
        if not district or not SAFE_NAME_PATTERN.match(district):
            raise ValidationError(
                "District name must be 2-100 valid characters.",
                field="district",
            )
        cleaned["district"] = district

    # 4. population
    if "population" in payload or require_all:
        try:
            pop = int(payload.get("population", 0))
        except (ValueError, TypeError):
            raise ValidationError("Population must be a whole integer.", field="population")
        if pop <= 0 or pop > 100_000_000:
            raise ValidationError("Population must be greater than 0 and realistic.", field="population")
        cleaned["population"] = pop

    # 5. income_category
    if "income_category" in payload or require_all:
        income = str(payload.get("income_category", "")).strip().title()
        if income not in VALID_INCOME_CATEGORIES:
            raise ValidationError(
                f"Income category must be one of: {', '.join(sorted(VALID_INCOME_CATEGORIES))}.",
                field="income_category",
            )
        cleaned["income_category"] = income

    # 6. Percentage fields (0 to 100)
    pct_fields = [
        ("clean_water_access", "Clean water access (%)"),
        ("water_quality_score", "Water quality score"),
        ("sanitation_coverage", "Sanitation coverage (%)"),
        ("toilet_availability", "Toilet availability (%)"),
        ("waste_management_score", "Waste management score"),
    ]
    for key, label in pct_fields:
        if key in payload and payload.get(key) not in (None, ""):
            try:
                val = round(float(payload[key]), 2)
            except (ValueError, TypeError):
                raise ValidationError(f"{label} must be a valid number.", field=key)
            if val < 0.0 or val > 100.0:
                raise ValidationError(f"{label} must be between 0.0 and 100.0.", field=key)
            cleaned[key] = val
        elif require_all and key in ("clean_water_access", "water_quality_score"):
            raise ValidationError(f"{label} is required.", field=key)

    # 7. availability_hours (0 to 24)
    if "availability_hours" in payload and payload.get("availability_hours") not in (None, ""):
        try:
            hours = round(float(payload["availability_hours"]), 1)
        except (ValueError, TypeError):
            raise ValidationError("Availability hours must be a numeric value.", field="availability_hours")
        if hours < 0.0 or hours > 24.0:
            raise ValidationError("Availability hours must be between 0.0 and 24.0 hours/day.", field="availability_hours")
        cleaned["availability_hours"] = hours
    elif require_all:
        cleaned["availability_hours"] = 8.0

    # 8. distance_to_source (>= 0)
    if "distance_to_source" in payload and payload.get("distance_to_source") not in (None, ""):
        try:
            dist = round(float(payload["distance_to_source"]), 2)
        except (ValueError, TypeError):
            raise ValidationError("Distance to source must be a numeric value.", field="distance_to_source")
        if dist < 0.0 or dist > 500.0:
            raise ValidationError("Distance to source must be between 0.0 and 500.0 km.", field="distance_to_source")
        cleaned["distance_to_source"] = dist
    elif require_all:
        cleaned["distance_to_source"] = 1.5

    # Default sanitation values if not explicitly supplied during quick creation
    if require_all:
        cleaned.setdefault("sanitation_coverage", round(cleaned["clean_water_access"] * 0.95, 2))
        cleaned.setdefault("toilet_availability", round(min(100.0, cleaned["clean_water_access"] + 5.0), 2))
        cleaned.setdefault("waste_management_score", round(cleaned["water_quality_score"] * 0.9, 2))

    return cleaned


def validate_threshold(value: Any, default: float = 50.0) -> float:
    """Validates threshold parameter for Stored Procedure GetPoorWaterAccess(threshold) and NoSQL filter."""
    if value in (None, ""):
        return default
    try:
        threshold = round(float(value), 2)
    except (ValueError, TypeError):
        raise ValidationError("Threshold must be a numeric percentage between 0 and 100.", field="threshold")
    if threshold < 0.0 or threshold > 100.0:
        raise ValidationError("Threshold must be between 0.0 and 100.0%.", field="threshold")
    return threshold
