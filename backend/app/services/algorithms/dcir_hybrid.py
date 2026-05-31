"""DCIR-Hybrid — departure-consistent iterative re-optimization (Route Optimizer, 2025)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.config import get_settings
from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput
from app.services.algorithms.metrics import leg_totals
from app.services.dcir import LegRefreshConfig, solve_dcir_hybrid
from app.services.profiles import build_profile_matrices

if TYPE_CHECKING:
    pass

META = AlgorithmMeta(
    id="dcir-hybrid",
    label="DCIR-Hybrid",
    paper="Departure-Consistent Iterative Re-optimization with Robust Traffic Profiles (2025)",
    year=2025,
    category="hybrid",
)


async def run(data: AlgorithmInput) -> AlgorithmOutput:
    settings = get_settings()
    profiles = data.profile_matrices or build_profile_matrices(data.duration_matrix)

    leg_refresh: Optional[LegRefreshConfig] = None
    if settings.dcir_refresh_legs and data.coords and settings.mapbox_access_token:
        leg_refresh = LegRefreshConfig(
            coords=data.coords,
            settings=settings,
            profile=str(data.extra.get("mode", settings.matrix_profile)),
            timezone=settings.dcir_timezone,
        )

    order, _ = await solve_dcir_hybrid(
        data.duration_matrix,
        profile_matrices=profiles,
        start_fixed=data.start_fixed,
        end_fixed=data.end_fixed,
        round_trip=data.round_trip,
        time_limit_s=data.time_limit_s or settings.dcir_time_limit_s,
        robust_lambda=settings.dcir_robust_lambda,
        leg_refresh=leg_refresh,
    )
    nominal = profiles[min(1, len(profiles) - 1)]
    dist, dur = leg_totals(order, data.distance_matrix, nominal, round_trip=data.round_trip)
    return AlgorithmOutput(
        order=order,
        total_duration_s=dur,
        total_distance_m=dist,
        meta=META,
        notes="Uses multi-profile traffic simulation when profiles are supplied.",
    )
