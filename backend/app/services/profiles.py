"""Traffic profiles and departure-consistent tour costing for DCIR."""

from __future__ import annotations

from dataclasses import dataclass

# Off-peak / nominal / peak duration multipliers (synthetic profiles).
PROFILE_FACTORS: tuple[float, ...] = (0.88, 1.0, 1.22)
PROFILE_LABELS: tuple[str, ...] = ("off_peak", "nominal", "peak")

# Cumulative tour-time thresholds (seconds) for profile selection during simulation.
PROFILE_TIME_THRESHOLDS_S: tuple[int, ...] = (0, 1800, 5400)


@dataclass(frozen=True)
class TourCostBreakdown:
    realized_s: int
    per_profile_s: tuple[int, ...]
    worst_profile_s: int


def build_profile_matrices(
    nominal: list[list[int]],
    *,
    factors: tuple[float, ...] = PROFILE_FACTORS,
) -> list[list[list[int]]]:
    """Build off-peak / nominal / peak duration matrices from one base matrix."""
    matrices: list[list[list[int]]] = []
    n = len(nominal)
    for factor in factors:
        scaled = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                raw = nominal[i][j]
                if raw >= 999_000_000:
                    scaled[i][j] = raw
                else:
                    scaled[i][j] = max(1, int(raw * factor))
        matrices.append(scaled)
    return matrices


def profile_index_for_elapsed(elapsed_s: int) -> int:
    idx = 0
    for i, threshold in enumerate(PROFILE_TIME_THRESHOLDS_S):
        if elapsed_s >= threshold:
            idx = i
    return min(idx, len(PROFILE_FACTORS) - 1)


def tour_cost_breakdown(
    order: list[int],
    profile_matrices: list[list[list[int]]],
    *,
    round_trip: bool,
    service_time_s: int = 0,
) -> TourCostBreakdown:
    per_profile = tuple(
        _simulate_cost(order, matrix, round_trip=round_trip, service_time_s=service_time_s)
        for matrix in profile_matrices
    )
    realized = _simulate_departure_consistent(
        order,
        profile_matrices,
        round_trip=round_trip,
        service_time_s=service_time_s,
    )
    return TourCostBreakdown(
        realized_s=realized,
        per_profile_s=per_profile,
        worst_profile_s=max(per_profile) if per_profile else realized,
    )


def robust_score(
    breakdown: TourCostBreakdown,
    *,
    lambda_robust: float,
) -> float:
    return breakdown.realized_s + lambda_robust * breakdown.worst_profile_s


def leg_drift_ratio(
    planned_s: int,
    refreshed_s: int,
    *,
    epsilon: float = 0.15,
) -> bool:
    if planned_s <= 0:
        return refreshed_s > 0
    return abs(refreshed_s - planned_s) / planned_s > epsilon


def _simulate_cost(
    order: list[int],
    duration_matrix: list[list[int]],
    *,
    round_trip: bool,
    service_time_s: int,
) -> int:
    if len(order) < 2:
        return 0

    path = list(order)
    if round_trip:
        path = path + [path[0]]

    total = 0
    for i in range(len(path) - 1):
        total += duration_matrix[path[i]][path[i + 1]]
        if i < len(path) - 2 and service_time_s:
            total += service_time_s
    return total


def _simulate_departure_consistent(
    order: list[int],
    profile_matrices: list[list[list[int]]],
    *,
    round_trip: bool,
    service_time_s: int,
) -> int:
    """Forward simulation: each leg uses the profile active at departure time."""
    if len(order) < 2:
        return 0

    nominal = profile_matrices[min(1, len(profile_matrices) - 1)]
    path = list(order)
    if round_trip:
        path = path + [path[0]]

    elapsed = 0
    total = 0
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        profile_idx = profile_index_for_elapsed(elapsed)
        matrix = profile_matrices[profile_idx]
        leg = matrix[a][b]
        total += leg
        elapsed += leg + service_time_s

    return total


def refreshed_leg_costs(
    order: list[int],
    profile_matrices: list[list[list[int]]],
    *,
    round_trip: bool,
    service_time_s: int = 0,
    drift_epsilon: float = 0.15,
) -> list[tuple[int, int, int, int]]:
    """
    Return drifted legs as (position_in_order, from_node, to_node, refreshed_cost).
    position indexes into `order` for the departing stop.
    """
    if len(order) < 2:
        return []

    nominal = profile_matrices[min(1, len(profile_matrices) - 1)]
    path = list(order)
    if round_trip:
        path = path + [path[0]]

    elapsed = 0
    drifts: list[tuple[int, int, int, int]] = []

    for leg_pos in range(len(path) - 1):
        a, b = path[leg_pos], path[leg_pos + 1]
        planned = nominal[a][b]
        profile_idx = profile_index_for_elapsed(elapsed)
        refreshed = profile_matrices[profile_idx][a][b]
        order_pos = leg_pos if leg_pos < len(order) else len(order) - 1
        if leg_drift_ratio(planned, refreshed, epsilon=drift_epsilon):
            drifts.append((order_pos, a, b, refreshed))
        elapsed += refreshed + service_time_s

    return drifts
