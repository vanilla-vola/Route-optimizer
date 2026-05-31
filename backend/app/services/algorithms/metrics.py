"""Leg totals from a visit order."""

from __future__ import annotations

from typing import Optional

from app.services.profiles import tour_cost_breakdown


def leg_totals(
    order: list[int],
    distance_matrix: list[list[int]],
    duration_matrix: list[list[int]],
    *,
    round_trip: bool,
) -> tuple[int, int]:
    if len(order) < 2:
        return 0, 0

    path = list(order)
    if round_trip:
        path = path + [path[0]]

    distance_m = 0
    duration_s = 0
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        distance_m += int(distance_matrix[a][b])
        duration_s += int(duration_matrix[a][b])
    return distance_m, duration_s


def realized_duration_s(
    order: list[int],
    profile_matrices: Optional[list[list[list[int]]]],
    *,
    round_trip: bool,
) -> Optional[int]:
    if not profile_matrices:
        return None
    return tour_cost_breakdown(
        order, profile_matrices, round_trip=round_trip
    ).realized_s
