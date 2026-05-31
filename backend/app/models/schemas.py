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
    realized_duration_s: Optional[int] = None


class AlgorithmInfo(BaseModel):
    id: str
    label: str
    paper: str
    year: int
    category: str
    supported_modes: list[str] = Field(default_factory=list)


class CompareProviderInfo(BaseModel):
    id: str
    label: str
    kind: str
    max_stops: Optional[int] = None
    requires_key: str = ""
    supported_modes: list[str] = Field(default_factory=list)


class CompareRequest(BaseModel):
    stops: list[Stop] = Field(..., min_length=2)
    start_fixed: bool = False
    end_fixed: bool = False
    round_trip: bool = True
    mode: str = TransportMode.DRIVING.value
    provider_ids: Optional[list[str]] = None

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        return normalize_mode(value)


class CompareResultItem(BaseModel):
    provider_id: str
    provider_label: str
    status: str
    order: Optional[list[int]] = None
    ordered_stops: Optional[list[OrderedStop]] = None
    total_duration_s: Optional[int] = None
    total_distance_m: Optional[int] = None
    vs_baseline_duration_pct: Optional[float] = None
    message: str = ""
    manual_url: Optional[str] = None
    is_baseline: bool = False


class CompareResponse(BaseModel):
    stop_count: int
    mode: str
    round_trip: bool
    profile_source: str
    metrics_note: str = ""
    results: list[CompareResultItem]


class BenchmarkRequest(BaseModel):
    stops: list[Stop] = Field(..., min_length=2)
    start_fixed: bool = False
    end_fixed: bool = False
    round_trip: bool = True
    mode: str = TransportMode.DRIVING.value
    algorithm_ids: Optional[list[str]] = None
    time_limit_s: int = Field(default=12, ge=2, le=30)

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        return normalize_mode(value)


class BenchmarkResultItem(BaseModel):
    algorithm_id: str
    algorithm_label: str
    paper: str
    year: int
    category: str
    status: str
    order: Optional[list[int]] = None
    total_duration_s: Optional[int] = None
    realized_duration_s: Optional[int] = None
    total_distance_m: Optional[int] = None
    vs_best_duration_pct: Optional[float] = None
    vs_best_realized_pct: Optional[float] = None
    notes: str = ""
    error: str = ""


class BenchmarkResponse(BaseModel):
    stop_count: int
    mode: str
    round_trip: bool
    profile_source: str
    results: list[BenchmarkResultItem]
    best_algorithm_id: Optional[str] = None
    best_realized_algorithm_id: Optional[str] = None
    ranking_note: str = (
        "Nominal = static matrix duration. Realized = departure-consistent traffic simulation."
    )
