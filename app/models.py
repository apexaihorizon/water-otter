"""
Domain Models using Python OOP Dataclasses.
Represents normalized relational entities (communities, water_quality, sanitation)
and denormalized NoSQL documents.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


@dataclass
class Community:
    """Represents a community record in the `communities` table/collection."""

    community_id: int
    community_name: str
    district: str
    population: int
    income_category: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WaterQuality:
    """Represents water access and quality metrics in the `water_quality` table/collection."""

    water_id: int
    community_id: int
    clean_water_access: float
    availability_hours: float
    distance_to_source: float
    water_quality_score: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def access_status(self) -> str:
        """Categorizes water access severity for analytical presentation."""
        if self.clean_water_access < 50.0:
            return "Critical (<50%)"
        if self.clean_water_access < 70.0:
            return "Moderate (50-69%)"
        return "Adequate (>=70%)"


@dataclass
class Sanitation:
    """Represents sanitation indicators in the `sanitation` table."""

    sanitation_id: int
    community_id: int
    sanitation_coverage: float
    toilet_availability: float
    waste_management_score: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CommunityProfile:
    """Composite OOP view model combining Community, WaterQuality, and Sanitation."""

    community: Community
    water_quality: WaterQuality
    sanitation: Optional[Sanitation] = None

    def to_flat_dict(self) -> Dict[str, Any]:
        data = {
            **self.community.to_dict(),
            **self.water_quality.to_dict(),
            "access_status": self.water_quality.access_status,
        }
        if self.sanitation:
            data.update(self.sanitation.to_dict())
        return data
