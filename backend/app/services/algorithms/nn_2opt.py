"""Nearest-neighbor + 2-opt (Lin & Kernighan family baseline)."""

from __future__ import annotations

from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput
from app.services.algorithms.metrics import leg_totals
from app.services.constructors import nearest_neighbor_2opt

META = AlgorithmMeta(
    id="nn-2opt",
    label="Nearest neighbor + 2-opt",
    paper="Lin & Kernighan (1973) local search family; NN + 2-opt baseline",
    year=1973,
    category="baseline",
)


async def run(data: AlgorithmInput) -> AlgorithmOutput:
    order = nearest_neighbor_2opt(data.duration_matrix, start=0)
    dist, dur = leg_totals(
        order, data.distance_matrix, data.duration_matrix, round_trip=data.round_trip
    )
    return AlgorithmOutput(order=order, total_duration_s=dur, total_distance_m=dist, meta=META)
