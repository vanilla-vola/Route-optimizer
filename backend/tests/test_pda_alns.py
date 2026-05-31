"""Tests for PDA-ALNS."""

import asyncio

from app.services.algorithms.base import AlgorithmInput
from app.services.algorithms.pda_alns import run as run_pda
from app.services.algorithms.dcir_hybrid import run as run_dcir
from app.services.constructors import tour_duration
from app.services.profiles import build_profile_matrices, tour_cost_breakdown


def _triangle_matrix() -> list[list[int]]:
    return [
        [0, 10, 15, 20],
        [12, 0, 8, 18],
        [14, 9, 0, 11],
        [22, 17, 10, 0],
    ]


def _input(matrix: list[list[int]]) -> AlgorithmInput:
    profiles = build_profile_matrices(matrix)
    n = len(matrix)
    return AlgorithmInput(
        duration_matrix=matrix,
        distance_matrix=[[0 if i == j else 1000 for j in range(n)] for i in range(n)],
        start_fixed=False,
        end_fixed=False,
        round_trip=True,
        time_limit_s=10,
        profile_matrices=profiles,
        coords=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),
    )


def test_pda_alns_returns_valid_permutation():
    matrix = _triangle_matrix()
    result = asyncio.run(run_pda(_input(matrix)))
    assert len(result.order) == 4
    assert sorted(result.order) == [0, 1, 2, 3]
    assert result.total_duration_s > 0


def test_pda_alns_realized_not_worse_than_seed_path_on_toy():
    matrix = _triangle_matrix()
    data = _input(matrix)
    profiles = data.profile_matrices or build_profile_matrices(matrix)

    result = asyncio.run(run_pda(data))
    realized = tour_cost_breakdown(result.order, profiles, round_trip=True).realized_s

    baseline_order = [0, 1, 2, 3]
    baseline_realized = tour_cost_breakdown(
        baseline_order, profiles, round_trip=True
    ).realized_s

    assert realized <= baseline_realized + 5


def test_pda_registered_meta():
    from app.services.algorithms.registry import get_algorithm

    meta, _ = get_algorithm("pda-alns")
    assert meta.id == "pda-alns"
    assert meta.year == 2025
