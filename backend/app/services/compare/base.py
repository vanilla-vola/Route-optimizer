"""Shared types for external provider comparison plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

from app.models.schemas import Stop


CompareStatus = Literal["ok", "skipped", "error", "manual"]


@dataclass(frozen=True)
class ProviderMeta:
    id: str
    label: str
    kind: str  # api | manual | internal
    max_stops: Optional[int] = None
    requires_key: str = ""


@dataclass
class CompareInput:
    stops: list[Stop]
    coords: tuple[tuple[float, float], ...]
    mode: str
    round_trip: bool
    start_fixed: bool
    end_fixed: bool
    duration_matrix: list[list[int]]
    distance_matrix: list[list[int]]
    profile_matrices: Optional[list[list[list[int]]]] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompareOutput:
    provider_id: str
    provider_label: str
    status: CompareStatus
    order: Optional[list[int]] = None
    total_duration_s: Optional[int] = None
    total_distance_m: Optional[int] = None
    vs_baseline_duration_pct: Optional[float] = None
    message: str = ""
    manual_url: Optional[str] = None
    is_baseline: bool = False
