"""Traffic-aware ALNS (T-ALNS-RRD, Scientific Reports 2025 — simplified)."""

from __future__ import annotations

import math
import random
import time

from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput
from app.services.algorithms.metrics import leg_totals
from app.services.constructors import tour_duration
from app.services.optimizer import FirstSolutionStrategy, solve_route
from app.services.profiles import build_profile_matrices, tour_cost_breakdown

META = AlgorithmMeta(
    id="td-alns-rrd",
    label="T-ALNS-RRD (traffic-aware)",
    paper="T-ALNS-RRD traffic-aware last-mile VRP (Scientific Reports, 2025)",
    year=2025,
    category="hybrid",
)


def _peak_destroy(tour: list[int], k: int, peak_matrix: list[list[int]]) -> tuple[list[int], list[int]]:
    costs: list[tuple[int, int]] = []
    for i in range(len(tour)):
        j = (i + 1) % len(tour)
        costs.append((peak_matrix[tour[i]][tour[j]], tour[i]))
    costs.sort(reverse=True)
    removed: set[int] = set()
    for _, node in costs:
        if node != tour[0] and len(removed) < k:
            removed.add(node)
    remaining = [n for n in tour if n not in removed]
    return remaining, list(removed)


def _regret_repair(tour: list[int], removed: list[int], matrix: list[list[int]]) -> list[int]:
    current = list(tour)
    for node in removed:
        best_pos, best = 0, math.inf
        for pos in range(len(current) + 1):
            if pos == 0:
                delta = matrix[node][current[0]] if current else 0
            elif pos == len(current):
                delta = matrix[current[-1]][node]
            else:
                i, j = current[pos - 1], current[pos]
                delta = matrix[i][node] + matrix[node][j] - matrix[i][j]
            if delta < best:
                best, best_pos = delta, pos
        current.insert(best_pos, node)
    return current


async def run(data: AlgorithmInput) -> AlgorithmOutput:
    matrix = data.duration_matrix
    profiles = data.profile_matrices or build_profile_matrices(matrix)
    peak = profiles[-1]
    rng = random.Random(7)
    deadline = time.monotonic() + max(3, data.time_limit_s)

    order, _ = solve_route(
        matrix,
        start_fixed=data.start_fixed,
        end_fixed=data.end_fixed,
        round_trip=data.round_trip,
        time_limit_s=max(1, data.time_limit_s // 4),
        first_solution_strategy=FirstSolutionStrategy.PATH_CHEAPEST_ARC,
    )
    best = list(order)
    current = list(best)
    k = max(2, len(matrix) // 4)

    while time.monotonic() < deadline:
        remaining, removed = _peak_destroy(current, k, peak)
        if not removed:
            break
        candidate = _regret_repair(remaining, removed, matrix)
        cand_realized = tour_cost_breakdown(candidate, profiles, round_trip=data.round_trip).realized_s
        best_realized = tour_cost_breakdown(best, profiles, round_trip=data.round_trip).realized_s
        if cand_realized <= best_realized:
            best = candidate
            current = candidate
        elif rng.random() < 0.2:
            current = candidate

    dist, dur = leg_totals(best, data.distance_matrix, matrix, round_trip=data.round_trip)
    return AlgorithmOutput(
        order=best,
        total_duration_s=dur,
        total_distance_m=dist,
        meta=META,
        notes="Destroy operator targets peak-traffic costly legs; scored on profile-aware duration.",
    )
