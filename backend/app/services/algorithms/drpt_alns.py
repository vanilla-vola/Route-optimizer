"""
DRPT-ALNS: Distributionally Robust Pareto-Temporal ALNS.

Research contribution: instead of ranking tours by one scalar objective during
search, this algorithm keeps a Pareto archive over nominal duration, realized
departure-consistent duration, worst-profile duration, CVaR-like tail duration,
and drift exposure. Destroy operators target legs that dominate the adversarial
tail profile, making the search explicitly robust to traffic-profile uncertainty.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass

from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput
from app.services.algorithms.metrics import leg_totals
from app.services.constructors import nearest_neighbor_2opt, regret_2_insertion, tour_duration
from app.services.optimizer import FirstSolutionStrategy, solve_route, solve_segment
from app.services.profiles import (
    build_profile_matrices,
    profile_index_for_elapsed,
    refreshed_leg_costs,
    tour_cost_breakdown,
)

META = AlgorithmMeta(
    id="drpt-alns",
    label="DRPT-ALNS (robust Pareto traffic)",
    paper=(
        "Distributionally Robust Pareto-Temporal ALNS for multi-stop routing "
        "under uncertain traffic-profile matrices (proposed, 2026)"
    ),
    year=2026,
    category="hybrid",
)

MAX_ARCHIVE_SIZE = 24
NOMINAL_EPSILON = 0.015
CVaR_ALPHA = 0.67
DRIFT_PENALTY = 0.12


@dataclass(frozen=True)
class TourMetrics:
    nominal_s: int
    realized_s: int
    worst_profile_s: int
    cvar_s: int
    drift_s: int


@dataclass(frozen=True)
class ArchiveItem:
    order: list[int]
    metrics: TourMetrics


def _profiles(data: AlgorithmInput) -> list[list[list[int]]]:
    return data.profile_matrices or build_profile_matrices(data.duration_matrix)


def _nominal_matrix(profiles: list[list[list[int]]]) -> list[list[int]]:
    return profiles[min(1, len(profiles) - 1)]


def _path(order: list[int], *, round_trip: bool) -> list[int]:
    if round_trip and order:
        return order + [order[0]]
    return list(order)


def _tail_mean(values: tuple[int, ...], alpha: float = CVaR_ALPHA) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    start = min(len(ordered) - 1, max(0, int(math.floor(len(ordered) * alpha))))
    tail = ordered[start:]
    return int(sum(tail) / len(tail))


def _drift_exposure(
    order: list[int],
    profiles: list[list[list[int]]],
    *,
    round_trip: bool,
) -> int:
    nominal = _nominal_matrix(profiles)
    exposure = 0
    for _, a, b, refreshed in refreshed_leg_costs(
        order, profiles, round_trip=round_trip
    ):
        exposure += abs(refreshed - nominal[a][b])
    return exposure


def _metrics(
    order: list[int],
    profiles: list[list[list[int]]],
    *,
    round_trip: bool,
) -> TourMetrics:
    nominal = _nominal_matrix(profiles)
    breakdown = tour_cost_breakdown(order, profiles, round_trip=round_trip)
    return TourMetrics(
        nominal_s=tour_duration(order, nominal, round_trip=round_trip),
        realized_s=breakdown.realized_s,
        worst_profile_s=breakdown.worst_profile_s,
        cvar_s=_tail_mean(breakdown.per_profile_s),
        drift_s=_drift_exposure(order, profiles, round_trip=round_trip),
    )


def _dominates(a: TourMetrics, b: TourMetrics) -> bool:
    a_vals = (a.nominal_s, a.realized_s, a.worst_profile_s, a.cvar_s, a.drift_s)
    b_vals = (b.nominal_s, b.realized_s, b.worst_profile_s, b.cvar_s, b.drift_s)
    return all(x <= y for x, y in zip(a_vals, b_vals)) and any(
        x < y for x, y in zip(a_vals, b_vals)
    )


def _robust_score(metrics: TourMetrics, best_nominal: int) -> float:
    nominal_gap = max(0.0, (metrics.nominal_s - best_nominal) / max(best_nominal, 1))
    return (
        metrics.realized_s
        + 0.35 * metrics.cvar_s
        + 0.20 * metrics.worst_profile_s
        + DRIFT_PENALTY * metrics.drift_s
        + 2.0 * metrics.realized_s * nominal_gap
    )


def _add_archive(
    archive: list[ArchiveItem],
    order: list[int],
    profiles: list[list[list[int]]],
    *,
    round_trip: bool,
) -> list[ArchiveItem]:
    key = tuple(order)
    if any(tuple(item.order) == key for item in archive):
        return archive

    candidate = ArchiveItem(
        order=list(order),
        metrics=_metrics(order, profiles, round_trip=round_trip),
    )
    if any(_dominates(item.metrics, candidate.metrics) for item in archive):
        return archive

    updated = [
        item for item in archive if not _dominates(candidate.metrics, item.metrics)
    ]
    updated.append(candidate)
    best_nominal = min(item.metrics.nominal_s for item in updated)
    updated.sort(key=lambda item: _robust_score(item.metrics, best_nominal))
    return updated[:MAX_ARCHIVE_SIZE]


def _profile_active_leg_cost(
    tour: list[int],
    pos: int,
    profiles: list[list[list[int]]],
    *,
    round_trip: bool,
) -> tuple[int, int, int]:
    path = _path(tour, round_trip=round_trip)
    if len(path) < 2:
        return 0, 0, 0

    pos = min(pos, len(path) - 2)
    elapsed = 0
    for i in range(pos):
        a, b = path[i], path[i + 1]
        elapsed += profiles[profile_index_for_elapsed(elapsed)][a][b]

    a, b = path[pos], path[pos + 1]
    profile_idx = profile_index_for_elapsed(elapsed)
    return a, b, profiles[profile_idx][a][b]


def _destroy_adversarial_tail(
    tour: list[int],
    profiles: list[list[list[int]]],
    *,
    round_trip: bool,
    k: int,
    rng: random.Random,
) -> tuple[list[int], list[int]]:
    """Remove stops around legs with large tail-profile or departure drift cost."""
    if len(tour) <= 2:
        return list(tour), []

    nominal = _nominal_matrix(profiles)
    scored: list[tuple[int, int]] = []
    path = _path(tour, round_trip=round_trip)
    for pos in range(len(path) - 1):
        a, b, active = _profile_active_leg_cost(
            tour, pos, profiles, round_trip=round_trip
        )
        worst = max(matrix[a][b] for matrix in profiles)
        score = max(active, worst) + abs(active - nominal[a][b])
        node_pos = pos if pos < len(tour) else 0
        if node_pos != 0:
            scored.append((score, tour[node_pos]))
        if pos + 1 < len(tour) and pos + 1 != 0:
            scored.append((score, tour[pos + 1]))

    if not scored:
        pool = tour[1:]
        removed = rng.sample(pool, min(k, len(pool)))
    else:
        scored.sort(reverse=True)
        removed = []
        for _, node in scored:
            if node not in removed:
                removed.append(node)
            if len(removed) >= k:
                break

    remaining = [node for node in tour if node not in set(removed)]
    return remaining, removed


def _destroy_pareto_archive_guided(
    current: list[int],
    archive: list[ArchiveItem],
    rng: random.Random,
    k: int,
) -> tuple[list[int], list[int]]:
    """Remove stops that disagree most with a randomly sampled Pareto elite."""
    if len(current) <= 2 or not archive:
        return _destroy_random(current, k, rng)

    elite = rng.choice(archive).order
    pos_current = {node: i for i, node in enumerate(current)}
    pos_elite = {node: i for i, node in enumerate(elite)}
    disagreement = sorted(
        (
            (abs(pos_current[node] - pos_elite.get(node, pos_current[node])), node)
            for node in current
            if node != current[0]
        ),
        reverse=True,
    )
    removed = [node for _, node in disagreement[:k]]
    remaining = [node for node in current if node not in set(removed)]
    return remaining, removed


def _destroy_random(
    tour: list[int],
    k: int,
    rng: random.Random,
) -> tuple[list[int], list[int]]:
    if len(tour) <= 2:
        return list(tour), []
    pool = tour[1:]
    removed = rng.sample(pool, min(k, len(pool)))
    remaining = [node for node in tour if node not in set(removed)]
    return remaining, removed


def _elapsed_before_pos(
    tour: list[int],
    pos: int,
    profiles: list[list[list[int]]],
) -> int:
    elapsed = 0
    for i in range(min(max(0, pos), max(0, len(tour) - 1))):
        a, b = tour[i], tour[i + 1]
        elapsed += profiles[profile_index_for_elapsed(elapsed)][a][b]
    return elapsed


def _insertion_delta(
    tour: list[int],
    pos: int,
    node: int,
    profiles: list[list[list[int]]],
    *,
    round_trip: bool,
) -> int:
    if not tour:
        return 0
    matrix = profiles[profile_index_for_elapsed(_elapsed_before_pos(tour, pos, profiles))]
    if pos <= 0:
        if len(tour) == 1:
            return matrix[node][tour[0]]
        return matrix[node][tour[0]] + matrix[tour[0]][tour[1]] - matrix[node][tour[1]]
    if pos >= len(tour):
        last = tour[-1]
        if round_trip:
            return matrix[last][node] + matrix[node][tour[0]] - matrix[last][tour[0]]
        return matrix[last][node]
    a, b = tour[pos - 1], tour[pos]
    return matrix[a][node] + matrix[node][b] - matrix[a][b]


def _repair_pareto_regret(
    tour: list[int],
    removed: list[int],
    profiles: list[list[list[int]]],
    *,
    round_trip: bool,
) -> list[int]:
    current = list(tour)
    pending = list(removed)
    while pending:
        best_node: int | None = None
        best_pos = 0
        best_key = (-math.inf, math.inf)
        for node in pending:
            costs = [
                (
                    _insertion_delta(
                        current, pos, node, profiles, round_trip=round_trip
                    ),
                    pos,
                )
                for pos in range(len(current) + 1)
            ]
            costs.sort(key=lambda item: item[0])
            best_cost, candidate_pos = costs[0]
            second_cost = costs[1][0] if len(costs) > 1 else best_cost
            regret = second_cost - best_cost
            key = (regret, -best_cost)
            if key > best_key:
                best_key = key
                best_node = node
                best_pos = candidate_pos
        if best_node is None:
            break
        current.insert(best_pos, best_node)
        pending.remove(best_node)
    return current


def _try_segment_polish(
    order: list[int],
    profiles: list[list[list[int]]],
    matrix: list[list[int]],
    *,
    round_trip: bool,
    time_limit_s: int,
) -> list[int]:
    drifts = refreshed_leg_costs(order, profiles, round_trip=round_trip)
    if not drifts:
        return order
    positions = sorted({pos for pos, _, _, _ in drifts})
    start = max(0, positions[0] - 1)
    end = min(len(order) - 1, positions[-1] + 1)
    segment = order[start : end + 1]
    if len(segment) < 3:
        return order
    try:
        improved = solve_segment(
            matrix,
            segment,
            round_trip=False,
            start_fixed=False,
            end_fixed=False,
            time_limit_s=max(1, time_limit_s),
            first_solution_strategy=FirstSolutionStrategy.PATH_CHEAPEST_ARC,
        )
    except Exception:
        return order
    candidate = order[:start] + improved + order[end + 1 :]
    old = _metrics(order, profiles, round_trip=round_trip)
    new = _metrics(candidate, profiles, round_trip=round_trip)
    return candidate if _robust_score(new, old.nominal_s) < _robust_score(old, old.nominal_s) else order


async def run(data: AlgorithmInput) -> AlgorithmOutput:
    profiles = _profiles(data)
    nominal = _nominal_matrix(profiles)
    matrix = data.duration_matrix
    rng = random.Random(73)
    deadline = time.monotonic() + max(4, data.time_limit_s)

    seeds: list[list[int]] = []
    for strategy in (
        FirstSolutionStrategy.PATH_CHEAPEST_ARC,
        FirstSolutionStrategy.CHRISTOFIDES,
        FirstSolutionStrategy.SAVINGS,
        FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION,
    ):
        if time.monotonic() >= deadline:
            break
        try:
            order, _ = solve_route(
                matrix,
                start_fixed=data.start_fixed,
                end_fixed=data.end_fixed,
                round_trip=data.round_trip,
                time_limit_s=1,
                first_solution_strategy=strategy,
            )
            seeds.append(order)
        except Exception:
            continue

    try:
        seeds.append(nearest_neighbor_2opt(matrix))
    except Exception:
        pass
    try:
        seeds.append(regret_2_insertion(matrix))
    except Exception:
        pass
    if not seeds:
        seeds = [list(range(len(matrix)))]

    archive: list[ArchiveItem] = []
    for seed in seeds:
        archive = _add_archive(
            archive, seed, profiles, round_trip=data.round_trip
        )

    current = min(
        archive,
        key=lambda item: _robust_score(
            item.metrics, min(a.metrics.nominal_s for a in archive)
        ),
    ).order

    ops = ("adversarial-tail", "pareto-guided", "random", "segment-polish")
    weights = [2.2, 1.4, 0.7, 1.2]
    rewards = [0.0 for _ in ops]
    uses = [0 for _ in ops]
    k = max(2, len(matrix) // 4)

    while time.monotonic() < deadline:
        best_nominal = min(item.metrics.nominal_s for item in archive)
        op_idx = rng.choices(range(len(ops)), weights=weights, k=1)[0]
        uses[op_idx] += 1
        op = ops[op_idx]

        if op == "segment-polish":
            candidate = _try_segment_polish(
                current,
                profiles,
                matrix,
                round_trip=data.round_trip,
                time_limit_s=1,
            )
        else:
            if op == "adversarial-tail":
                remaining, removed = _destroy_adversarial_tail(
                    current, profiles, round_trip=data.round_trip, k=k, rng=rng
                )
            elif op == "pareto-guided":
                remaining, removed = _destroy_pareto_archive_guided(
                    current, archive, rng, k
                )
            else:
                remaining, removed = _destroy_random(current, k, rng)

            if not removed:
                break
            candidate = _repair_pareto_regret(
                remaining, removed, profiles, round_trip=data.round_trip
            )

        before = _metrics(current, profiles, round_trip=data.round_trip)
        after = _metrics(candidate, profiles, round_trip=data.round_trip)
        before_score = _robust_score(before, best_nominal)
        after_score = _robust_score(after, best_nominal)

        archive_before = len(archive)
        archive = _add_archive(
            archive, candidate, profiles, round_trip=data.round_trip
        )
        archive_grew = len(archive) > archive_before

        if after_score <= before_score or archive_grew:
            current = candidate
            rewards[op_idx] += 2.0 if archive_grew else 1.0
        elif rng.random() < 0.05:
            current = candidate

        for idx in range(len(ops)):
            if uses[idx]:
                weights[idx] = max(0.2, 0.5 + rewards[idx] / uses[idx])

    best_nominal = min(item.metrics.nominal_s for item in archive)
    feasible = [
        item
        for item in archive
        if item.metrics.nominal_s <= int(best_nominal * (1.0 + NOMINAL_EPSILON)) + 1
    ]
    chosen = min(
        feasible or archive,
        key=lambda item: _robust_score(item.metrics, best_nominal),
    )

    dist, dur = leg_totals(
        chosen.order, data.distance_matrix, nominal, round_trip=data.round_trip
    )
    return AlgorithmOutput(
        order=chosen.order,
        total_duration_s=dur,
        total_distance_m=dist,
        meta=META,
        notes=(
            "Maintains a Pareto archive over nominal, realized, worst-profile, "
            "CVaR-tail, and drift exposure; final tour minimizes robust score "
            f"within {NOMINAL_EPSILON:.1%} nominal slack."
        ),
    )
