"""
DCIR-Hybrid: Departure-Consistent Iterative Re-optimization with Robust Traffic Profiles.

Phases:
  1. Ensemble construction (OR-Tools seeds + classical constructors)
  2. Robust tour selection across traffic profiles
  3. Departure-consistent drift patching (+ optional Mapbox leg refresh)
  4. POPMUSIC-style sliding-window GLS patches
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from app.services.constructors import (
    nearest_neighbor_2opt,
    regret_2_insertion,
    tour_duration,
)
from app.services.optimizer import FirstSolutionStrategy, solve_route, solve_segment
from app.services.profiles import (
    TourCostBreakdown,
    build_profile_matrices,
    profile_index_for_elapsed,
    refreshed_leg_costs,
    robust_score,
    tour_cost_breakdown,
)

if TYPE_CHECKING:
    from app.config import Settings

_FS = FirstSolutionStrategy

ENSEMBLE_STRATEGIES: tuple[tuple[int, str], ...] = (
    (_FS.PATH_CHEAPEST_ARC, "path_cheapest_arc"),
    (_FS.CHRISTOFIDES, "christofides"),
    (_FS.SAVINGS, "savings"),
    (_FS.PARALLEL_CHEAPEST_INSERTION, "parallel_insertion"),
)


@dataclass(frozen=True)
class LegRefreshConfig:
    coords: tuple[tuple[float, float], ...]
    settings: Settings
    profile: str
    timezone: str
    max_refreshes_per_iteration: int = 4


async def solve_dcir_hybrid(
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
    leg_refresh: Optional[LegRefreshConfig] = None,
) -> tuple[list[int], int]:
    n = len(duration_matrix)
    if n <= 1:
        return list(range(n)), 0

    profiles = _copy_profile_matrices(
        profile_matrices or build_profile_matrices(duration_matrix)
    )
    working_matrix = [row[:] for row in duration_matrix]
    nominal = profiles[min(1, len(profiles) - 1)]
    deadline = time.monotonic() + time_limit_s

    def remaining() -> int:
        return max(1, int(deadline - time.monotonic()))

    pool = _phase1_ensemble(
        working_matrix,
        start_fixed=start_fixed,
        end_fixed=end_fixed,
        round_trip=round_trip,
        budget_s=max(2, int(time_limit_s * 0.45)),
        per_seed_s=max(1, min(2, time_limit_s // 6)),
    )

    best_order, _best_breakdown = _phase2_select(
        pool,
        profiles,
        round_trip=round_trip,
        robust_lambda=robust_lambda,
    )

    if remaining() > 2 and n >= 4:
        best_order = await _phase3_dcir_loop(
            best_order,
            working_matrix,
            profiles,
            start_fixed=start_fixed,
            end_fixed=end_fixed,
            round_trip=round_trip,
            max_iterations=max_dcir_iterations,
            budget_s=max(2, int(time_limit_s * 0.35)),
            leg_refresh=leg_refresh,
        )

    if remaining() > 1 and n >= popmusic_window:
        best_order = _phase4_popmusic(
            best_order,
            working_matrix,
            profiles,
            start_fixed=start_fixed,
            end_fixed=end_fixed,
            round_trip=round_trip,
            window=popmusic_window,
            stride=popmusic_stride,
            budget_s=remaining(),
        )

    nominal_total = tour_duration(best_order, nominal, round_trip=round_trip)

    # Phase 5: nominal GLS polish — ensure we don't sacrifice static matrix quality.
    polish_budget = remaining()
    if polish_budget >= 1 and n >= 3:
        try:
            polished, _ = solve_route(
                duration_matrix,
                start_fixed=start_fixed,
                end_fixed=end_fixed,
                round_trip=round_trip,
                time_limit_s=polish_budget,
                first_solution_strategy=_FS.PATH_CHEAPEST_ARC,
            )
            if tour_duration(polished, nominal, round_trip=round_trip) < nominal_total:
                best_order = polished
                nominal_total = tour_duration(polished, nominal, round_trip=round_trip)
        except Exception:
            pass

    return best_order, nominal_total


def _copy_profile_matrices(
    matrices: list[list[list[int]]],
) -> list[list[list[int]]]:
    return [[row[:] for row in matrix] for matrix in matrices]


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
    """Pick best nominal duration; use robust score only as tie-break within 1%."""
    nominal_matrix = profile_matrices[min(1, len(profile_matrices) - 1)]
    scored: list[tuple[list[int], TourCostBreakdown, int]] = []

    for order in pool:
        breakdown = tour_cost_breakdown(
            order, profile_matrices, round_trip=round_trip
        )
        nominal_s = tour_duration(order, nominal_matrix, round_trip=round_trip)
        scored.append((order, breakdown, nominal_s))

    scored.sort(key=lambda item: item[2])
    best_order, best_breakdown, best_nominal = scored[0]
    threshold = int(best_nominal * 1.01) + 1

    near_best = [item for item in scored if item[2] <= threshold]
    if len(near_best) == 1:
        return best_order, best_breakdown

    order, breakdown, _ = min(
        near_best,
        key=lambda item: robust_score(item[1], lambda_robust=robust_lambda),
    )
    return order, breakdown


async def _phase3_dcir_loop(
    order: list[int],
    duration_matrix: list[list[int]],
    profile_matrices: list[list[list[int]]],
    *,
    start_fixed: bool,
    end_fixed: bool,
    round_trip: bool,
    max_iterations: int,
    budget_s: int,
    leg_refresh: Optional[LegRefreshConfig],
) -> list[int]:
    from app.services.matrix_profiles import next_departure_times, parse_depart_hours

    current = list(order)
    deadline = time.monotonic() + budget_s
    per_iter_s = max(1, budget_s // max(1, max_iterations))

    depart_times: list[str] = []
    if leg_refresh:
        try:
            hours = parse_depart_hours(leg_refresh.settings.dcir_depart_hours)
            depart_times = next_departure_times(hours, timezone=leg_refresh.timezone)
        except Exception:
            leg_refresh = None

    for _ in range(max_iterations):
        if time.monotonic() >= deadline:
            break

        if leg_refresh and depart_times:
            await _refresh_drifted_legs(
                current,
                duration_matrix,
                profile_matrices,
                round_trip=round_trip,
                leg_refresh=leg_refresh,
                depart_times=depart_times,
            )

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


async def _refresh_drifted_legs(
    order: list[int],
    duration_matrix: list[list[int]],
    profile_matrices: list[list[list[int]]],
    *,
    round_trip: bool,
    leg_refresh: LegRefreshConfig,
    depart_times: list[str],
) -> None:
    from app.services.matrix_profiles import apply_leg_refresh_to_matrix, refresh_leg_duration

    if len(order) < 2:
        return

    path = list(order)
    if round_trip:
        path = path + [path[0]]

    elapsed = 0
    refreshed = 0

    for leg_pos in range(len(path) - 1):
        if refreshed >= leg_refresh.max_refreshes_per_iteration:
            break

        a, b = path[leg_pos], path[leg_pos + 1]
        profile_idx = profile_index_for_elapsed(elapsed)
        planned = profile_matrices[min(1, len(profile_matrices) - 1)][a][b]
        profile_cost = profile_matrices[profile_idx][a][b]

        if abs(profile_cost - planned) / max(planned, 1) <= 0.15:
            elapsed += profile_cost
            continue

        depart_at = depart_times[min(profile_idx, len(depart_times) - 1)]
        duration_s = await refresh_leg_duration(
            leg_refresh.coords[a],
            leg_refresh.coords[b],
            settings=leg_refresh.settings,
            profile=leg_refresh.profile,
            depart_at=depart_at,
        )
        if duration_s is None:
            elapsed += profile_cost
            continue

        apply_leg_refresh_to_matrix(duration_matrix, a, b, duration_s)
        for matrix in profile_matrices:
            apply_leg_refresh_to_matrix(matrix, a, b, duration_s)

        refreshed += 1
        elapsed += duration_s


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
