"""Input order baseline (no optimization)."""

from __future__ import annotations

from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput
from app.services.algorithms.metrics import leg_totals

META = AlgorithmMeta(
    id="input-order",
    label="Input order (no optimization)",
    paper="Baseline: visit stops in the order they were added",
    year=0,
    category="baseline",
)


async def run(data: AlgorithmInput) -> AlgorithmOutput:
    n = len(data.duration_matrix)
    order = list(range(n))
    dist, dur = leg_totals(
        order, data.distance_matrix, data.duration_matrix, round_trip=data.round_trip
    )
    return AlgorithmOutput(order=order, total_duration_s=dur, total_distance_m=dist, meta=META)
