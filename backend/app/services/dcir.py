"""
DCIR-Hybrid: Departure-Consistent Iterative Re-optimization with Robust Traffic Profiles.

Phases:
  1. Ensemble construction (OR-Tools seeds + classical constructors)
  2. Robust tour selection across traffic profiles
  3. Departure-consistent drift patching
  4. POPMUSIC-style sliding-window GLS patches
"""

from __future__ import annotations

import time

from app.services.constructors import (
    nearest_neighbor_2opt,
    regret_2_insertion,
    tour_duration,
)
from app.services.optimizer import FirstSolutionStrategy, solve_route, solve_segment
from app.services.profiles import (
    TourCostBreakdown,
    build_profile_matrices,
    refreshed_leg_costs,
    robust_score,
    tour_cost_breakdown,
)

_FS = FirstSolutionStrategy

ENSEMBLE_STRATEGIES: tuple[tuple[int, str], ...] = (
    (_FS.PATH_CHEAPEST_ARC, "path_cheapest_arc"),
    (_FS.CHRISTOFIDES, "christofides"),
    (_FS.SAVINGS, "savings"),
    (_FS.PARALLEL_CHEAPEST_INSERTION, "parallel_insertion"),
)


def solve_dcir_hybrid(
    duration_matrix: list[list[int]],
    *,
    start_fixed: bool,
    end_fixed: bool,
    round_trip: bool,
    time_limit_s: int = 12,
    robust_lambda: float = 0.3,
    profile_matrices: list[list[list[int]]] | None = None,
    max_dcir_iterations: int = 4,
    popmusic_window: int = 7,
    popmusic_stride: int = 3,
) -> tuple[list[int], int]:
    n = len(duration_matrix)
    if n <= 1:
        return list(range(n)), 0

    profiles = profile_matrices or build_profile_matrices(duration_matrix)
    nominal = profiles[min(1, len(profiles) - 1)]
    deadline = time.monotonic() + time_limit_s

    def remaining() -> int:
        return max(1, int(deadline - time.monotonic()))

    # --- Phase 1: ensemble construction ---
    pool = _phase1_ensemble(
        duration_matrix,
        start_fixed=start_fixed,
        end_fixed=end_fixed,
        round_trip=round_trip,
        budget_s=max(2, int(time_limit_s * 0.45)),
        per_seed_s=max(1, min(2, time_limit_s // 6)),
    )

    # --- Phase 2: robust selection ---
    best_order, best_breakdown = _phase2_select(
        pool,
        profiles,
        round_trip=round_trip,
        robust_lambda=robust_lambda,
    )

    # --- Phase 3: departure-consistent re-optimization ---
    if remaining() > 2 and n >= 4:
        best_order = _phase3_dcir_loop(
            best_order,
            duration_matrix,
            profiles,
            start_fixed=start_fixed,
            end_fixed=end_fixed,
            round_trip=round_trip,
            max_iterations=max_dcir_iterations,
            budget_s=max(2, int(time_limit_s * 0.35)),
        )
        best_breakdown = tour_cost_breakdown(
            best_order, profiles, round_trip=round_trip
        )

    # --- Phase 4: POPMUSIC patches ---
    if remaining() > 1 and n >= popmusic_window:
        best_order = _phase4_popmusic(
            best_order,
            duration_matrix,
            profiles,
            start_fixed=start_fixed,
            end_fixed=end_fixed,
            round_trip=round_trip,
            window=popmusic_window,
            stride=popmusic_stride,
            budget_s=remaining(),
        )

    final_breakdown = tour_cost_breakdown(best_order, profiles, round_trip=round_trip)
    # Report total on nominal matrix so API legs match sum(total_duration_s).
    nominal_total = tour_duration(best_order, nominal, round_trip=round_trip)
    _ = final_breakdown  # used for internal optimization; nominal for response consistency
    return best_order, nominal_total


def _phase1_ensemble(
    duration_matrix: list[list[int]],
    *,
    start_fixed: bool,
    end_fixed: bool,
    round_trip: bool,
    budget_s: int,
    per_seed_s: int,
) -> list[list[int]]:
    seen: set[tuple[int, ...]] = set()
    pool: list[list[int]] = []

    def add(order: list[int]) -> None:
        key = tuple(order)
        if key not in seen:
            seen.add(key)
            pool.append(order)

    seed_deadline = time.monotonic() + budget_s
    for strategy, _ in ENSEMBLE_STRATEGIES:
        if time.monotonic() >= seed_deadline:
            break
        try:
            order, _ = solve_route(
                duration_matrix,
                start_fixed=start_fixed,
                end_fixed=end_fixed,
                round_trip=round_trip,
                time_limit_s=per_seed_s,
                first_solution_strategy=strategy,
            )
            add(order)
        except Exception:
            continue

    try:
        add(nearest_neighbor_2opt(duration_matrix, start=0))
    except Exception:
        pass

    try:
        add(regret_2_insertion(duration_matrix, start=0))
    except Exception:
        pass

    if not pool:
        order, _ = solve_route(
            duration_matrix,
            start_fixed=start_fixed,
            end_fixed=end_fixed,
            round_trip=round_trip,
            time_limit_s=per_seed_s,
        )
        pool.append(order)

    return pool


def _phase2_select(
    pool: list[list[int]],
    profile_matrices: list[list[list[int]]],
    *,
    round_trip: bool,
    robust_lambda: float,
) -> tuple[list[int], TourCostBreakdown]:
    best_order = pool[0]
    best_score = float("inf")
    best_breakdown = tour_cost_breakdown(
        best_order, profile_matrices, round_trip=round_trip
    )

    for order in pool:
        breakdown = tour_cost_breakdown(
            order, profile_matrices, round_trip=round_trip
        )
        score = robust_score(breakdown, lambda_robust=robust_lambda)
        if score < best_score:
            best_score = score
            best_order = order
            best_breakdown = breakdown

    return best_order, best_breakdown


def _phase3_dcir_loop(
    order: list[int],
    duration_matrix: list[list[int]],
    profile_matrices: list[list[list[int]]],
    *,
    start_fixed: bool,
    end_fixed: bool,
    round_trip: bool,
    max_iterations: int,
    budget_s: int,
) -> list[int]:
    current = list(order)
    deadline = time.monotonic() + budget_s
    per_iter_s = max(1, budget_s // max(1, max_iterations))

    for _ in range(max_iterations):
        if time.monotonic() >= deadline:
            break

        drifts = refreshed_leg_costs(
            current, profile_matrices, round_trip=round_trip
        )
        if not drifts:
            break

        positions = {pos for pos, _, _, _ in drifts}
        start_pos = max(0, min(positions) - 1)
        end_pos = min(len(current) - 1, max(positions) + 1)

        segment_nodes = current[start_pos : end_pos + 1]
        if len(segment_nodes) < 3:
            break

        seg_start_fixed = start_fixed and start_pos == 0
        seg_end_fixed = end_fixed and end_pos == len(current) - 1

        try:
            improved_segment = solve_segment(
                duration_matrix,
                segment_nodes,
                round_trip=False,
                start_fixed=seg_start_fixed,
                end_fixed=seg_end_fixed,
                time_limit_s=per_iter_s,
                first_solution_strategy=_FS.PATH_CHEAPEST_ARC,
            )
        except Exception:
            break

        candidate = current[:start_pos] + improved_segment + current[end_pos + 1 :]

        old_cost = tour_cost_breakdown(
            current, profile_matrices, round_trip=round_trip
        ).realized_s
        new_cost = tour_cost_breakdown(
            candidate, profile_matrices, round_trip=round_trip
        ).realized_s

        if new_cost <= old_cost:
            current = candidate

    return current


def _phase4_popmusic(
    order: list[int],
    duration_matrix: list[list[int]],
    profile_matrices: list[list[list[int]]],
    *,
    start_fixed: bool,
    end_fixed: bool,
    round_trip: bool,
    window: int,
    stride: int,
    budget_s: int,
) -> list[int]:
    current = list(order)
    deadline = time.monotonic() + budget_s
    n = len(current)

    for start in range(0, max(1, n - window + 1), stride):
        if time.monotonic() >= deadline:
            break
        end = min(n, start + window)
        segment = current[start:end]
        if len(segment) < 3:
            continue

        seg_start_fixed = start_fixed and start == 0
        seg_end_fixed = end_fixed and end == n

        try:
            improved = solve_segment(
                duration_matrix,
                segment,
                round_trip=False,
                start_fixed=seg_start_fixed,
                end_fixed=seg_end_fixed,
                time_limit_s=1,
                first_solution_strategy=_FS.PATH_CHEAPEST_ARC,
            )
        except Exception:
            continue

        candidate = current[:start] + improved + current[end:]
        old_realized = tour_cost_breakdown(
            current, profile_matrices, round_trip=round_trip
        ).realized_s
        new_realized = tour_cost_breakdown(
            candidate, profile_matrices, round_trip=round_trip
        ).realized_s

        if new_realized < old_realized:
            current = candidate

    return current
