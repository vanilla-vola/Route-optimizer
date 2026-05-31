"""Lightweight tour constructors used as DCIR ensemble seeds."""

from __future__ import annotations

import math


def nearest_neighbor_2opt(
    duration_matrix: list[list[int]],
    *,
    start: int = 0,
    max_2opt_passes: int = 50,
) -> list[int]:
    n = len(duration_matrix)
    if n <= 1:
        return list(range(n))

    unvisited = set(range(n))
    unvisited.discard(start)
    tour = [start]

    while unvisited:
        last = tour[-1]
        nxt = min(unvisited, key=lambda j: duration_matrix[last][j])
        tour.append(nxt)
        unvisited.remove(nxt)

    return _two_opt(tour, duration_matrix, max_passes=max_2opt_passes)


def regret_2_insertion(
    duration_matrix: list[list[int]],
    *,
    start: int = 0,
) -> list[int]:
    n = len(duration_matrix)
    if n <= 1:
        return list(range(n))

    remaining = [i for i in range(n) if i != start]
    if not remaining:
        return [start]

    # Seed with the closest node to start.
    first = min(remaining, key=lambda j: duration_matrix[start][j])
    tour = [start, first]
    remaining.remove(first)

    while remaining:
        best_node = -1
        best_pos = -1
        best_regret = -math.inf

        for node in remaining:
            best_cost = math.inf
            second_cost = math.inf
            best_insert_pos = 1

            for pos in range(1, len(tour) + 1):
                i = tour[pos - 1]
                if pos == len(tour):
                    delta = duration_matrix[i][node]
                else:
                    j = tour[pos]
                    delta = (
                        duration_matrix[i][node]
                        + duration_matrix[node][j]
                        - duration_matrix[i][j]
                    )
                if delta < best_cost:
                    second_cost = best_cost
                    best_cost = delta
                    best_insert_pos = pos
                elif delta < second_cost:
                    second_cost = delta

            regret = second_cost - best_cost if math.isfinite(second_cost) else best_cost
            if regret > best_regret:
                best_regret = regret
                best_node = node
                best_pos = best_insert_pos

        tour.insert(best_pos, best_node)
        remaining.remove(best_node)

    return tour


def _two_opt(
    tour: list[int],
    duration_matrix: list[list[int]],
    *,
    max_passes: int,
) -> list[int]:
    n = len(tour)
    if n < 4:
        return tour

    improved = True
    passes = 0
    while improved and passes < max_passes:
        improved = False
        passes += 1
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                a, b = tour[i - 1], tour[i]
                c, d = tour[j], tour[j + 1]
                delta = (
                    duration_matrix[a][c]
                    + duration_matrix[b][d]
                    - duration_matrix[a][b]
                    - duration_matrix[c][d]
                )
                if delta < 0:
                    tour[i : j + 1] = reversed(tour[i : j + 1])
                    improved = True
    return tour


def tour_duration(
    order: list[int],
    duration_matrix: list[list[int]],
    *,
    round_trip: bool,
) -> int:
    if len(order) < 2:
        return 0

    path = list(order)
    if round_trip:
        path = path + [path[0]]

    total = 0
    for i in range(len(path) - 1):
        total += duration_matrix[path[i]][path[i + 1]]
    return total
