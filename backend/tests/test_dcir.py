"""Tests for DCIR-Hybrid components."""

from app.services.constructors import nearest_neighbor_2opt, tour_duration
from app.services.dcir import solve_dcir_hybrid
from app.services.optimizer import solve_route
from app.services.profiles import (
    build_profile_matrices,
    tour_cost_breakdown,
)


def _triangle_matrix() -> list[list[int]]:
    # 4 nodes: asymmetric durations to make order matter.
    return [
        [0, 10, 15, 20],
        [12, 0, 8, 18],
        [14, 9, 0, 11],
        [22, 17, 10, 0],
    ]


def test_build_profile_matrices_scales():
    nominal = _triangle_matrix()
    profiles = build_profile_matrices(nominal)
    assert len(profiles) == 3
    assert profiles[1][0][1] == nominal[0][1]
    assert profiles[2][0][1] > nominal[0][1]
    assert profiles[0][0][1] < nominal[0][1]


def test_tour_cost_breakdown_realized():
    order = [0, 2, 1, 3]
    profiles = build_profile_matrices(_triangle_matrix())
    breakdown = tour_cost_breakdown(order, profiles, round_trip=True)
    assert breakdown.realized_s > 0
    assert breakdown.worst_profile_s >= breakdown.realized_s or breakdown.worst_profile_s > 0


def test_dcir_returns_valid_tour():
    matrix = _triangle_matrix()
    order, total = solve_dcir_hybrid(
        matrix,
        start_fixed=False,
        end_fixed=False,
        round_trip=True,
        time_limit_s=8,
    )
    assert len(order) == 4
    assert len(set(order)) == 4
    assert total == tour_duration(order, matrix, round_trip=True)


def test_dcir_not_worse_than_single_seed_on_toy():
    matrix = _triangle_matrix()
    baseline_order, baseline_total = solve_route(
        matrix,
        start_fixed=False,
        end_fixed=False,
        round_trip=True,
        time_limit_s=3,
    )
    dcir_order, dcir_total = solve_dcir_hybrid(
        matrix,
        start_fixed=False,
        end_fixed=False,
        round_trip=True,
        time_limit_s=10,
    )
    profiles = build_profile_matrices(matrix)
    baseline_realized = tour_cost_breakdown(
        baseline_order, profiles, round_trip=True
    ).realized_s
    dcir_realized = tour_cost_breakdown(
        dcir_order, profiles, round_trip=True
    ).realized_s
    assert dcir_total <= baseline_total + 1 or dcir_realized <= baseline_realized + 1


def test_nearest_neighbor_2opt_visits_all():
    matrix = _triangle_matrix()
    tour = nearest_neighbor_2opt(matrix)
    assert sorted(tour) == [0, 1, 2, 3]
