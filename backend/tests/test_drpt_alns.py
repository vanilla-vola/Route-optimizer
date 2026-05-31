"""Smoke tests for DRPT-ALNS."""

import asyncio

from app.services.algorithms.base import AlgorithmInput
from app.services.algorithms.drpt_alns import run as run_drpt
from app.services.profiles import build_profile_matrices, tour_cost_breakdown


def _matrix() -> list[list[int]]:
    return [
        [0, 10, 40, 30, 25],
        [12, 0, 15, 35, 30],
        [42, 15, 0, 12, 18],
        [32, 34, 10, 0, 14],
        [24, 28, 16, 14, 0],
    ]


def _input(matrix: list[list[int]]) -> AlgorithmInput:
    n = len(matrix)
    return AlgorithmInput(
        duration_matrix=matrix,
        distance_matrix=[[0 if i == j else 1000 for j in range(n)] for i in range(n)],
        start_fixed=False,
        end_fixed=False,
        round_trip=True,
        time_limit_s=6,
        profile_matrices=build_profile_matrices(matrix),
    )


def test_drpt_alns_returns_valid_tour():
    matrix = _matrix()
    result = asyncio.run(run_drpt(_input(matrix)))
    assert sorted(result.order) == list(range(len(matrix)))
    assert result.total_duration_s > 0


def test_drpt_alns_has_realized_cost():
    matrix = _matrix()
    data = _input(matrix)
    result = asyncio.run(run_drpt(data))
    realized = tour_cost_breakdown(
        result.order,
        data.profile_matrices or build_profile_matrices(matrix),
        round_trip=True,
    ).realized_s
    assert realized > 0


def test_drpt_registered_meta():
    from app.services.algorithms.registry import get_algorithm

    meta, _ = get_algorithm("drpt-alns")
    assert meta.id == "drpt-alns"
    assert meta.year == 2026
