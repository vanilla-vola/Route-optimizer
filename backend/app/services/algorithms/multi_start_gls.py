"""Multi-start construction ensemble + best GLS (Vidal HGS-style, 2012)."""

from __future__ import annotations

import time

from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput
from app.services.algorithms.metrics import leg_totals
from app.services.constructors import nearest_neighbor_2opt, regret_2_insertion, tour_duration
from app.services.optimizer import FirstSolutionStrategy, solve_route

META = AlgorithmMeta(
    id="multi-start-gls",
    label="Multi-start GLS",
    paper="Hybrid Genetic Search construction diversity (Vidal et al., 2012)",
    year=2012,
    category="hybrid",
)

STRATEGIES = (
    FirstSolutionStrategy.PATH_CHEAPEST_ARC,
    FirstSolutionStrategy.CHRISTOFIDES,
    FirstSolutionStrategy.SAVINGS,
    FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION,
)


async def run(data: AlgorithmInput) -> AlgorithmOutput:
    matrix = data.duration_matrix
    deadline = time.monotonic() + max(3, data.time_limit_s)
    per_seed = max(1, data.time_limit_s // (len(STRATEGIES) + 2))
    pool: list[list[int]] = []

    for strategy in STRATEGIES:
        if time.monotonic() >= deadline:
            break
        try:
            order, _ = solve_route(
                matrix,
                start_fixed=data.start_fixed,
                end_fixed=data.end_fixed,
                round_trip=data.round_trip,
                time_limit_s=per_seed,
                first_solution_strategy=strategy,
            )
            pool.append(order)
        except Exception:
            continue

    pool.append(nearest_neighbor_2opt(matrix))
    pool.append(regret_2_insertion(matrix))

    best = pool[0]
    best_cost = tour_duration(best, matrix, round_trip=data.round_trip)
    for order in pool[1:]:
        cost = tour_duration(order, matrix, round_trip=data.round_trip)
        if cost < best_cost:
            best, best_cost = order, cost

    remaining = max(1, int(deadline - time.monotonic()))
    try:
        polished, _ = solve_route(
            matrix,
            start_fixed=data.start_fixed,
            end_fixed=data.end_fixed,
            round_trip=data.round_trip,
            time_limit_s=remaining,
            first_solution_strategy=FirstSolutionStrategy.PATH_CHEAPEST_ARC,
        )
        if tour_duration(polished, matrix, round_trip=data.round_trip) < best_cost:
            best = polished
    except Exception:
        pass

    dist, dur = leg_totals(best, data.distance_matrix, matrix, round_trip=data.round_trip)
    return AlgorithmOutput(order=best, total_duration_s=dur, total_distance_m=dist, meta=META)
