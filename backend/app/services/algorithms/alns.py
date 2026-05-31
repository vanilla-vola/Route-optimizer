"""Adaptive Large Neighborhood Search (Shaw 1998; Pisinger & Ropke 2019)."""

from __future__ import annotations

import math
import random
import time

from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput
from app.services.algorithms.metrics import leg_totals
from app.services.constructors import nearest_neighbor_2opt, regret_2_insertion, tour_duration
from app.services.optimizer import FirstSolutionStrategy, solve_route

META = AlgorithmMeta(
    id="alns",
    label="ALNS",
    paper="Adaptive Large Neighborhood Search (Pisinger & Ropke, 2019 handbook)",
    year=2019,
    category="metaheuristic",
)


def _insertion_cost(tour: list[int], pos: int, node: int, matrix: list[list[int]]) -> int:
    if pos == 0:
        return matrix[node][tour[0]] if tour else 0
    if pos >= len(tour):
        return matrix[tour[-1]][node]
    i, j = tour[pos - 1], tour[pos]
    return matrix[i][node] + matrix[node][j] - matrix[i][j]


def _best_insertion(tour: list[int], node: int, matrix: list[list[int]]) -> tuple[int, int]:
    best_pos, best_cost = 0, math.inf
    for pos in range(len(tour) + 1):
        cost = _insertion_cost(tour, pos, node, matrix)
        if cost < best_cost:
            best_cost, best_pos = cost, pos
    return best_pos, int(best_cost)


def _destroy_random(tour: list[int], k: int, rng: random.Random) -> tuple[list[int], list[int]]:
    if len(tour) <= k + 1:
        k = max(1, len(tour) // 3)
    removed = rng.sample(tour[1:] if len(tour) > 1 else tour, min(k, max(1, len(tour) - 1)))
    remaining = [n for n in tour if n not in removed]
    return remaining, removed


def _destroy_worst(tour: list[int], k: int, matrix: list[list[int]]) -> tuple[list[int], list[int]]:
    if len(tour) < 3:
        return _destroy_random(tour, k, random.Random(0))
    edge_costs: list[tuple[int, int, int]] = []
    for i in range(len(tour) - 1):
        edge_costs.append((matrix[tour[i]][tour[i + 1]], tour[i], tour[i + 1]))
    if len(tour) > 2:
        edge_costs.append((matrix[tour[-1]][tour[0]], tour[-1], tour[0]))
    edge_costs.sort(reverse=True)
    removed: set[int] = set()
    for _, a, b in edge_costs:
        if len(removed) >= k:
            break
        if a != tour[0]:
            removed.add(a)
        if b != tour[0] and len(removed) < k:
            removed.add(b)
    remaining = [n for n in tour if n not in removed]
    return remaining, list(removed)


def _repair(tour: list[int], removed: list[int], matrix: list[list[int]]) -> list[int]:
    current = list(tour)
    for node in removed:
        pos, _ = _best_insertion(current, node, matrix)
        current.insert(pos, node)
    return current


async def run(data: AlgorithmInput) -> AlgorithmOutput:
    matrix = data.duration_matrix
    rng = random.Random(42)
    deadline = time.monotonic() + max(2, data.time_limit_s)

    try:
        seed, _ = solve_route(
            matrix,
            start_fixed=data.start_fixed,
            end_fixed=data.end_fixed,
            round_trip=data.round_trip,
            time_limit_s=max(1, data.time_limit_s // 3),
            first_solution_strategy=FirstSolutionStrategy.PATH_CHEAPEST_ARC,
        )
    except Exception:
        seed = nearest_neighbor_2opt(matrix)

    best = list(seed)
    best_cost = tour_duration(best, matrix, round_trip=data.round_trip)
    current = list(best)

    ops = ["random", "worst"]
    weights = [1.0, 1.0]
    scores = [0.0, 0.0]
    uses = [0, 0]

    k = max(2, len(matrix) // 4)
    while time.monotonic() < deadline:
        op_idx = rng.choices(range(2), weights=weights, k=1)[0]
        uses[op_idx] += 1
        if ops[op_idx] == "random":
            remaining, removed = _destroy_random(current, k, rng)
        else:
            remaining, removed = _destroy_worst(current, k, matrix)
        if not removed:
            break
        candidate = _repair(remaining, removed, matrix)
        cand_cost = tour_duration(candidate, matrix, round_trip=data.round_trip)
        if cand_cost <= best_cost:
            best, best_cost = candidate, cand_cost
            scores[op_idx] += 2.0
            current = candidate
        elif cand_cost <= tour_duration(current, matrix, round_trip=data.round_trip):
            current = candidate
            scores[op_idx] += 1.0
        else:
            current = regret_2_insertion(matrix) if rng.random() < 0.15 else candidate

        for i in range(2):
            if uses[i] > 0:
                weights[i] = max(0.1, scores[i] / uses[i])

    dist, dur = leg_totals(best, data.distance_matrix, matrix, round_trip=data.round_trip)
    return AlgorithmOutput(order=best, total_duration_s=dur, total_distance_m=dist, meta=META)
