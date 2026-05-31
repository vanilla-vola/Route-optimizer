"""Regret-2 insertion construction (no OR-Tools polish)."""

from __future__ import annotations

from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput
from app.services.algorithms.metrics import leg_totals
from app.services.constructors import regret_2_insertion

META = AlgorithmMeta(
    id="regret-2-insertion",
    label="Regret-2 insertion",
    paper="Regret insertion heuristics (Ropke & Pisinger, ALNS repair operators)",
    year=2006,
    category="classical",
)


async def run(data: AlgorithmInput) -> AlgorithmOutput:
    order = regret_2_insertion(data.duration_matrix, start=0)
    dist, dur = leg_totals(
        order, data.distance_matrix, data.duration_matrix, round_trip=data.round_trip
    )
    return AlgorithmOutput(order=order, total_duration_s=dur, total_distance_m=dist, meta=META)
