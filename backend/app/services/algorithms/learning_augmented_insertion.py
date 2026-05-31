"""Learning-augmented insertion with robust traffic profiles (Gouleakis et al., AAAI 2023)."""

from __future__ import annotations

from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput
from app.services.algorithms.metrics import leg_totals
from app.services.constructors import regret_2_insertion, tour_duration
from app.services.optimizer import FirstSolutionStrategy, solve_route
from app.services.profiles import build_profile_matrices, robust_score, tour_cost_breakdown

META = AlgorithmMeta(
    id="learning-augmented-insertion",
    label="Learning-augmented insertion",
    paper="Learning-augmented online TSP (Gouleakis, Lakis & Shahkarami, AAAI 2023)",
    year=2023,
    category="learning",
)


async def run(data: AlgorithmInput) -> AlgorithmOutput:
    matrix = data.duration_matrix
    profiles = data.profile_matrices or build_profile_matrices(matrix)

    candidates = [
        regret_2_insertion(matrix),
    ]
    try:
        gls_order, _ = solve_route(
            matrix,
            start_fixed=data.start_fixed,
            end_fixed=data.end_fixed,
            round_trip=data.round_trip,
            time_limit_s=max(2, data.time_limit_s // 2),
            first_solution_strategy=FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION,
        )
        candidates.append(gls_order)
    except Exception:
        pass

    best = candidates[0]
    best_score = float("inf")
    for order in candidates:
        breakdown = tour_cost_breakdown(order, profiles, round_trip=data.round_trip)
        score = robust_score(breakdown, lambda_robust=0.35)
        if score < best_score:
            best_score = score
            best = order

    dist, dur = leg_totals(best, data.distance_matrix, matrix, round_trip=data.round_trip)
    return AlgorithmOutput(
        order=best,
        total_duration_s=dur,
        total_distance_m=dist,
        meta=META,
        notes="Robust profile-augmented scoring when predictions (profiles) disagree.",
    )
