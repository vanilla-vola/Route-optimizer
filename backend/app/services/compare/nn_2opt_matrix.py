"""NN + 2-opt baseline on the same matrix."""

from __future__ import annotations

from app.config import Settings
from app.services.algorithms.base import AlgorithmInput
from app.services.algorithms.nn_2opt import run as run_nn
from app.services.compare.base import CompareInput, CompareOutput, ProviderMeta

META = ProviderMeta(
    id="nn-2opt-matrix",
    label="NN + 2-opt (same matrix)",
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
        time_limit_s=settings.solver_time_limit_s,
    )
    result = await run_nn(algo_input)
    return CompareOutput(
        provider_id=META.id,
        provider_label=META.label,
        status="ok",
        order=result.order,
        total_duration_s=result.total_duration_s,
        total_distance_m=result.total_distance_m,
        message="Classic nearest-neighbor + 2-opt baseline on the same matrix.",
    )
