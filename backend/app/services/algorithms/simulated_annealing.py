"""Simulated annealing for TSP."""

from __future__ import annotations

import math
import random
import time

from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput
from app.services.algorithms.metrics import leg_totals
from app.services.constructors import nearest_neighbor_2opt, tour_duration

META = AlgorithmMeta(
    id="simulated-annealing",
    label="Simulated annealing",
    paper="Kirkpatrick et al. (1983); classic TSP metaheuristic",
    year=1983,
    category="metaheuristic",
)


def _two_opt_swap(tour: list[int], i: int, j: int) -> list[int]:
    new_tour = tour[:]
    new_tour[i : j + 1] = reversed(new_tour[i : j + 1])
    return new_tour


async def run(data: AlgorithmInput) -> AlgorithmOutput:
    matrix = data.duration_matrix
    rng = random.Random(11)
    current = nearest_neighbor_2opt(matrix)
    best = list(current)
    best_cost = tour_duration(best, matrix, round_trip=data.round_trip)
    current_cost = best_cost

    deadline = time.monotonic() + max(2, data.time_limit_s)
    n = len(current)
    temp = max(1.0, current_cost / 10.0)
    cooling = 0.995

    while time.monotonic() < deadline and temp > 0.01:
        i = rng.randint(1, n - 2)
        j = rng.randint(i + 1, n - 1)
        candidate = _two_opt_swap(current, i, j)
        cand_cost = tour_duration(candidate, matrix, round_trip=data.round_trip)
        delta = cand_cost - current_cost
        if delta < 0 or rng.random() < math.exp(-delta / temp):
            current, current_cost = candidate, cand_cost
            if cand_cost < best_cost:
                best, best_cost = candidate, cand_cost
        temp *= cooling

    dist, dur = leg_totals(best, data.distance_matrix, matrix, round_trip=data.round_trip)
    return AlgorithmOutput(order=best, total_duration_s=dur, total_distance_m=dist, meta=META)
