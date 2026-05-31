"""Christofides (1976) construction + GLS polish."""

from __future__ import annotations

from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput
from app.services.algorithms.metrics import leg_totals
from app.services.optimizer import FirstSolutionStrategy, solve_route

META = AlgorithmMeta(
    id="christofides-gls",
    label="Christofides + GLS",
    paper="Christofides (1976) 3/2 metric TSP + Guided Local Search",
    year=1976,
    category="classical",
)


async def run(data: AlgorithmInput) -> AlgorithmOutput:
    order, _ = solve_route(
        data.duration_matrix,
        start_fixed=data.start_fixed,
        end_fixed=data.end_fixed,
        round_trip=data.round_trip,
        time_limit_s=data.time_limit_s,
        first_solution_strategy=FirstSolutionStrategy.CHRISTOFIDES,
    )
    dist, dur = leg_totals(
        order, data.distance_matrix, data.duration_matrix, round_trip=data.round_trip
    )
    return AlgorithmOutput(
        order=order,
        total_duration_s=dur,
        total_distance_m=dist,
        meta=META,
        notes="Christofides guarantee applies only to metric symmetric instances.",
    )
