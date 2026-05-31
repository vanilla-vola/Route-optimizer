"""POPMUSIC sliding-window decomposition (Taillard & Voß, 2002)."""

from __future__ import annotations

import time

from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput
from app.services.algorithms.metrics import leg_totals
from app.services.constructors import tour_duration
from app.services.optimizer import FirstSolutionStrategy, solve_route, solve_segment

META = AlgorithmMeta(
    id="popmusic-gls",
    label="POPMUSIC + GLS",
    paper="POPMUSIC template (Taillard & Voß, 2002) with OR-Tools segment GLS",
    year=2002,
    category="metaheuristic",
)


async def run(data: AlgorithmInput) -> AlgorithmOutput:
    matrix = data.duration_matrix
    per_seed = max(1, data.time_limit_s // 3)
    order, _ = solve_route(
        matrix,
        start_fixed=data.start_fixed,
        end_fixed=data.end_fixed,
        round_trip=data.round_trip,
        time_limit_s=per_seed,
        first_solution_strategy=FirstSolutionStrategy.PATH_CHEAPEST_ARC,
    )

    window = min(9, max(5, len(order) // 2))
    stride = max(2, window // 2)
    deadline = time.monotonic() + max(2, data.time_limit_s - per_seed)
    current = list(order)

    for start in range(0, max(1, len(current) - window + 1), stride):
        if time.monotonic() >= deadline:
            break
        end = min(len(current), start + window)
        segment = current[start:end]
        if len(segment) < 3:
            continue
        try:
            improved = solve_segment(
                matrix,
                segment,
                round_trip=False,
                start_fixed=data.start_fixed and start == 0,
                end_fixed=data.end_fixed and end == len(current),
                time_limit_s=1,
                first_solution_strategy=FirstSolutionStrategy.PATH_CHEAPEST_ARC,
            )
        except Exception:
            continue
        candidate = current[:start] + improved + current[end:]
        if tour_duration(candidate, matrix, round_trip=data.round_trip) < tour_duration(
            current, matrix, round_trip=data.round_trip
        ):
            current = candidate

    dist, dur = leg_totals(current, data.distance_matrix, matrix, round_trip=data.round_trip)
    return AlgorithmOutput(order=current, total_duration_s=dur, total_distance_m=dist, meta=META)
