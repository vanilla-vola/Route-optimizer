"""TuneNSearch-style warm-start transfer (2025) — fast ensemble pick + long GLS."""

from __future__ import annotations

import time

from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput
from app.services.algorithms.metrics import leg_totals
from app.services.constructors import nearest_neighbor_2opt, regret_2_insertion, tour_duration
from app.services.optimizer import FirstSolutionStrategy, solve_route

META = AlgorithmMeta(
    id="tunesearch-warmstart-gls",
    label="TuneNSearch warm-start",
    paper="TuneNSearch transfer learning + local search for VRP (2025)",
    year=2025,
    category="learning",
)


async def run(data: AlgorithmInput) -> AlgorithmOutput:
    matrix = data.duration_matrix
    quick = max(1, min(2, data.time_limit_s // 5))
    candidates: list[list[int]] = []

    for strategy in (
        FirstSolutionStrategy.PATH_CHEAPEST_ARC,
        FirstSolutionStrategy.CHRISTOFIDES,
        FirstSolutionStrategy.SAVINGS,
    ):
        try:
            order, _ = solve_route(
                matrix,
                start_fixed=data.start_fixed,
                end_fixed=data.end_fixed,
                round_trip=data.round_trip,
                time_limit_s=quick,
                first_solution_strategy=strategy,
            )
            candidates.append(order)
        except Exception:
            continue

    candidates.extend([nearest_neighbor_2opt(matrix), regret_2_insertion(matrix)])

    best_seed = min(
        candidates,
        key=lambda o: tour_duration(o, matrix, round_trip=data.round_trip),
    )

    polish_time = max(2, data.time_limit_s - quick * 3)
    order, _ = solve_route(
        matrix,
        start_fixed=data.start_fixed,
        end_fixed=data.end_fixed,
        round_trip=data.round_trip,
        time_limit_s=polish_time,
        first_solution_strategy=FirstSolutionStrategy.PATH_CHEAPEST_ARC,
    )

    if tour_duration(order, matrix, round_trip=data.round_trip) > tour_duration(
        best_seed, matrix, round_trip=data.round_trip
    ):
        order = best_seed

    dist, dur = leg_totals(order, data.distance_matrix, matrix, round_trip=data.round_trip)
    return AlgorithmOutput(
        order=order,
        total_duration_s=dur,
        total_distance_m=dist,
        meta=META,
        notes="Simplified TuneNSearch: transfer best quick construction into GLS polish.",
    )
