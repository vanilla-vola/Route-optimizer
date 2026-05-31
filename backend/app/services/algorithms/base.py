"""Shared types for routing algorithm plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class AlgorithmMeta:
    id: str
    label: str
    paper: str
    year: int
    category: str  # classical | metaheuristic | hybrid | learning | baseline


@dataclass
class AlgorithmInput:
    duration_matrix: list[list[int]]
    distance_matrix: list[list[int]]
    start_fixed: bool = False
    end_fixed: bool = False
    round_trip: bool = True
    time_limit_s: int = 8
    profile_matrices: Optional[list[list[list[int]]]] = None
    coords: Optional[tuple[tuple[float, float], ...]] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AlgorithmOutput:
    order: list[int]
    total_duration_s: int
    total_distance_m: int
    meta: AlgorithmMeta
    notes: str = ""
