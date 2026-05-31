"""Route Optimizer DCIR-Hybrid (internal baseline)."""

from __future__ import annotations

from app.config import Settings
from app.services.algorithms.base import AlgorithmInput
from app.services.algorithms.dcir_hybrid import run as run_dcir
from app.services.compare.base import CompareInput, CompareOutput, ProviderMeta

META = ProviderMeta(
    id="route-optimizer",
    label="Route Optimizer (DCIR-Hybrid)",
    kind="internal",
    max_stops=25,
)


async def compare(data: CompareInput, settings: Settings) -> CompareOutput:
    algo_input = AlgorithmInput(
        duration_matrix=data.duration_matrix,
        distance_matrix=data.distance_matrix,
        start_fixed=data.start_fixed,
        end_fixed=data.end_fixed,
        round_trip=data.round_trip,
        time_limit_s=settings.dcir_time_limit_s,
        profile_matrices=data.profile_matrices,
        coords=data.coords,
        extra={"mode": data.mode},
    )
    result = await run_dcir(algo_input)
    return CompareOutput(
        provider_id=META.id,
        provider_label=META.label,
        status="ok",
        order=result.order,
        total_duration_s=result.total_duration_s,
        total_distance_m=result.total_distance_m,
        is_baseline=True,
        message=result.notes,
    )
