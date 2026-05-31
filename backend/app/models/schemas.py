from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.transport_modes import TransportMode, normalize_mode


class Stop(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    name: str = Field(default="", max_length=120)


class PlaceSuggestion(BaseModel):
    name: str = Field(..., max_length=120)
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    subtitle: str = Field(default="", max_length=200)


class OptimizeRequest(BaseModel):
    stops: list[Stop] = Field(..., min_length=2)
    start_fixed: bool = False
    end_fixed: bool = False
    round_trip: bool = True
    mode: str = TransportMode.DRIVING.value

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        return normalize_mode(value)


class Leg(BaseModel):
    from_index: int
    to_index: int
    distance_m: int
    duration_s: int


class OrderedStop(BaseModel):
    """One stop in the optimized visit sequence."""

    sequence: int
    index: int
    name: str
    lat: float
    lng: float


class OptimizeResponse(BaseModel):
    order: list[int]
    ordered_stops: list[OrderedStop]
    total_distance_m: int
    total_duration_s: int
    legs: list[Leg]
    mode: str
    round_trip: bool
    solver: str = "ortools-gls"
    profile_source: Optional[str] = None
