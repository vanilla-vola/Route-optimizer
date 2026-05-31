"""
Profile-Drift ALNS (PDA-ALNS).

IEEE-oriented extension: destroy operators target legs where departure-consistent
cost diverges from nominal; repair uses profile-aware regret insertion and
segment re-optimization; acceptance optimizes realized duration under a nominal
epsilon constraint.
"""

from __future__ import annotations

import math
import random
import time

from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput
from app.services.algorithms.metrics import leg_totals
from app.services.constructors import nearest_neighbor_2opt, tour_duration
from app.services.optimizer import FirstSolutionStrategy, solve_route, solve_segment
from app.services.profiles import (
    build_profile_matrices,
    profile_index_for_elapsed,
    refreshed_leg_costs,
    tour_cost_breakdown,
)

META = AlgorithmMeta(
    id="pda-alns",
    label="PDA-ALNS (profile-drift ALNS)",
    paper=(
        "Profile-Drift Adaptive Large Neighborhood Search for departure-consistent "
        "routing under multi-layer traffic matrices (proposed, 2025)"
    ),
    year=2025,
    category="hybrid",
)

# Nominal slack when updating the incumbent (matches DCIR Phase-2 tie band).
NOMINAL_EPSILON = 0.01


def _profiles(data: AlgorithmInput) -> list[list[list[int]]]:
    return data.profile_matrices or build_profile_matrices(data.duration_matrix)


def _nominal_matrix(profiles: list[list[list[int]]]) -> list[list[int]]:
    return profiles[min(1, len(profiles) - 1)]


def _realized(order: list[int], profiles: list[list[list[int]]], *, round_trip: bool) -> int:
    return tour_cost_breakdown(order, profiles, round_trip=round_trip).realized_s


def _elapsed_before_pos(tour: list[int], pos: int, profiles: list[list[list[int]]]) -> int:
    elapsed = 0
    for i in range(min(max(0, pos), max(0, len(tour) - 1))):
        a, b = tour[i], tour[i + 1]
        pidx = profile_index_for_elapsed(elapsed)
        elapsed += profiles[pidx][a][b]
    return elapsed


def _matrix_at_insertion(
    tour: list[int],
    pos: int,
    profiles: list[list[list[int]]],
) -> list[list[int]]:
    return profiles[profile_index_for_elapsed(_elapsed_before_pos(tour, pos, profiles))]


def _insertion_delta(
    tour: list[int],
    pos: int,
    node: int,
    matrix: list[list[int]],
    *,
    round_trip: bool,
) -> int:
    if not tour:
        return 0
    if pos <= 0:
        if len(tour) == 1:
            return matrix[node][tour[0]]
        return matrix[node][tour[0]] + matrix[tour[0]][tour[1]] - matrix[node][tour[1]]
    if pos >= len(tour):
        last = tour[-1]
        if round_trip:
            return matrix[last][node] + matrix[node][tour[0]] - matrix[last][tour[0]]
        return matrix[last][node]
    i, j = tour[pos - 1], tour[pos]
    return matrix[i][node] + matrix[node][j] - matrix[i][j]


def _regret_repair_profile(
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
        best_regret = -math.inf
        for node in pending:
            best_cost = math.inf
            second_cost = math.inf
            best_insert_pos = 0
            for pos in range(len(current) + 1):
                matrix = _matrix_at_insertion(current, pos, profiles)
                delta = _insertion_delta(
                    current, pos, node, matrix, round_trip=round_trip
                )
                if delta < best_cost:
                    second_cost = best_cost
                    best_cost = delta
                    best_insert_pos = pos
                elif delta < second_cost:
                    second_cost = delta
            regret = (
                second_cost - best_cost
                if math.isfinite(second_cost)
                else best_cost
            )
            if regret > best_regret:
                best_regret = regret
                best_node = node
                best_pos = best_insert_pos
        if best_node is None:
            break
        current.insert(best_pos, best_node)
        pending.remove(best_node)
    return current


def _destroy_random(tour: list[int], k: int, rng: random.Random) -> tuple[list[int], list[int]]:
    if len(tour) <= 2:
        return tour[:], []
    pool = tour[1:] if len(tour) > 1 else tour[:]
    k = min(k, max(1, len(pool)))
    removed = rng.sample(pool, k)
    remaining = [n for n in tour if n not in removed]
    return remaining, removed


def _destroy_drift_segment(
    tour: list[int],
    profiles: list[list[list[int]]],
    *,
    round_trip: bool,
    k: int,
    start_fixed: bool,
) -> tuple[list[int], list[int], int | None, int | None]:
    """
    Remove nodes on a contiguous block covering drifted legs.
    Returns (remaining, removed, segment_start, segment_end) for optional segment repair.
    """
    drifts = refreshed_leg_costs(tour, profiles, round_trip=round_trip)
    if not drifts:
        return tour[:], [], None, None

    positions = sorted({pos for pos, _, _, _ in drifts})
    seg_start = max(0, positions[0])
    seg_end = min(len(tour) - 1, positions[-1])

    if seg_end - seg_start < 1 and len(positions) >= 2:
        seg_start = max(0, positions[0] - 1)
        seg_end = min(len(tour) - 1, positions[-1] + 1)

    removed: list[int] = []
    for idx in range(seg_start, seg_end + 1):
        if idx == 0 and start_fixed:
            continue
        if idx < len(tour):
            removed.append(tour[idx])

    if len(removed) < k:
        for pos, _, _, _ in sorted(drifts, key=lambda x: -x[3])[:k]:
            node = tour[pos] if pos < len(tour) else tour[-1]
            if node not in removed and not (pos == 0 and start_fixed):
                removed.append(node)
            if len(removed) >= k:
                break

    removed_set = set(removed)
    remaining = [n for n in tour if n not in removed_set]
    return remaining, removed, seg_start, seg_end


def _repair_segment(
    tour: list[int],
    seg_start: int,
    seg_end: int,
    matrix: list[list[int]],
    *,
    start_fixed: bool,
    end_fixed: bool,
    round_trip: bool,
    time_limit_s: int,
) -> list[int]:
    if seg_start is None or seg_end is None or seg_end - seg_start < 1:
        return tour
    segment = tour[seg_start : seg_end + 1]
    if len(segment) < 3:
        return tour
    improved = solve_segment(
        matrix,
        segment,
        round_trip=False,
        start_fixed=start_fixed and seg_start == 0,
        end_fixed=end_fixed and seg_end == len(tour) - 1,
        time_limit_s=max(1, time_limit_s),
        first_solution_strategy=FirstSolutionStrategy.PATH_CHEAPEST_ARC,
    )
    return tour[:seg_start] + improved + tour[seg_end + 1 :]


def _within_nominal_eps(
    candidate: list[int],
    best_nominal: int,
    nominal_matrix: list[list[int]],
    *,
    round_trip: bool,
    epsilon: float = NOMINAL_EPSILON,
) -> bool:
    if best_nominal <= 0:
        return True
    cand_nom = tour_duration(candidate, nominal_matrix, round_trip=round_trip)
    return cand_nom <= int(best_nominal * (1.0 + epsilon)) + 1


async def run(data: AlgorithmInput) -> AlgorithmOutput:
    matrix = data.duration_matrix
    profiles = _profiles(data)
    nominal = _nominal_matrix(profiles)
    rng = random.Random(42)
    deadline = time.monotonic() + max(3, data.time_limit_s)

    try:
        seed, _ = solve_route(
            matrix,
            start_fixed=data.start_fixed,
            end_fixed=data.end_fixed,
            round_trip=data.round_trip,
            time_limit_s=max(1, data.time_limit_s // 4),
            first_solution_strategy=FirstSolutionStrategy.PATH_CHEAPEST_ARC,
        )
    except Exception:
        seed = nearest_neighbor_2opt(matrix)

    best = list(seed)
    current = list(best)
    best_realized = _realized(best, profiles, round_trip=data.round_trip)
    best_nominal = tour_duration(best, nominal, round_trip=data.round_trip)

    ops = ["drift", "segment", "regret", "random"]
    weights = [2.0, 1.5, 1.5, 0.8]
    scores = [0.0] * len(ops)
    uses = [0] * len(ops)

    k = max(2, len(matrix) // 4)
    seg_budget = max(1, data.time_limit_s // 8)

    while time.monotonic() < deadline:
        op_idx = rng.choices(range(len(ops)), weights=weights, k=1)[0]
        uses[op_idx] += 1
        seg_start: int | None = None
        seg_end: int | None = None

        if ops[op_idx] == "drift":
            remaining, removed, seg_start, seg_end = _destroy_drift_segment(
                current,
                profiles,
                round_trip=data.round_trip,
                k=k,
                start_fixed=data.start_fixed,
            )
            if not removed:
                remaining, removed = _destroy_random(current, k, rng)
        elif ops[op_idx] == "segment":
            _, removed, seg_start, seg_end = _destroy_drift_segment(
                current,
                profiles,
                round_trip=data.round_trip,
                k=k,
                start_fixed=data.start_fixed,
            )
            if seg_start is not None and seg_end is not None:
                candidate = _repair_segment(
                    current,
                    seg_start,
                    seg_end,
                    matrix,
                    start_fixed=data.start_fixed,
                    end_fixed=data.end_fixed,
                    round_trip=data.round_trip,
                    time_limit_s=seg_budget,
                )
                cand_real = _realized(candidate, profiles, round_trip=data.round_trip)
                cur_real = _realized(current, profiles, round_trip=data.round_trip)
                if cand_real <= cur_real and _within_nominal_eps(
                    candidate, best_nominal, nominal, round_trip=data.round_trip
                ):
                    current = candidate
                    if cand_real < best_realized:
                        best, best_realized = candidate, cand_real
                        best_nominal = tour_duration(best, nominal, round_trip=data.round_trip)
                        scores[op_idx] += 2.0
                uses[op_idx] -= 1
                continue
            remaining, removed = _destroy_random(current, k, rng)
        elif ops[op_idx] == "regret":
            remaining, removed = _destroy_random(current, max(2, k // 2), rng)
        else:
            remaining, removed = _destroy_random(current, k, rng)

        if not removed:
            break

        if ops[op_idx] in ("drift", "regret"):
            candidate = _regret_repair_profile(
                remaining, removed, profiles, round_trip=data.round_trip
            )
        else:
            candidate = _regret_repair_profile(
                remaining, removed, profiles, round_trip=data.round_trip
            )

        cand_real = _realized(candidate, profiles, round_trip=data.round_trip)
        cur_real = _realized(current, profiles, round_trip=data.round_trip)

        accepted = False
        if cand_real < best_realized and _within_nominal_eps(
            candidate, best_nominal, nominal, round_trip=data.round_trip
        ):
            best, best_realized = candidate, cand_real
            best_nominal = tour_duration(best, nominal, round_trip=data.round_trip)
            current = candidate
            accepted = True
            scores[op_idx] += 2.0
        elif cand_real <= cur_real:
            current = candidate
            accepted = True
            scores[op_idx] += 1.0
        elif rng.random() < 0.08:
            current = candidate

        if not accepted and seg_start is not None and time.monotonic() < deadline:
            seg_candidate = _repair_segment(
                current,
                seg_start,
                seg_end or seg_start,
                matrix,
                start_fixed=data.start_fixed,
                end_fixed=data.end_fixed,
                round_trip=data.round_trip,
                time_limit_s=seg_budget,
            )
            seg_real = _realized(seg_candidate, profiles, round_trip=data.round_trip)
            if seg_real <= best_realized and _within_nominal_eps(
                seg_candidate, best_nominal, nominal, round_trip=data.round_trip
            ):
                best, best_realized = seg_candidate, seg_real
                best_nominal = tour_duration(best, nominal, round_trip=data.round_trip)
                current = seg_candidate

        for i in range(len(ops)):
            if uses[i] > 0:
                weights[i] = max(0.2, 0.5 + scores[i] / uses[i])

    if time.monotonic() < deadline and len(matrix) >= 3:
        try:
            polished, _ = solve_route(
                matrix,
                start_fixed=data.start_fixed,
                end_fixed=data.end_fixed,
                round_trip=data.round_trip,
                time_limit_s=max(1, int(deadline - time.monotonic())),
                first_solution_strategy=FirstSolutionStrategy.PATH_CHEAPEST_ARC,
            )
            pol_real = _realized(polished, profiles, round_trip=data.round_trip)
            pol_nom = tour_duration(polished, nominal, round_trip=data.round_trip)
            if pol_real <= best_realized and pol_nom <= int(best_nominal * (1.0 + NOMINAL_EPSILON)) + 1:
                best = polished
            elif pol_nom < tour_duration(best, nominal, round_trip=data.round_trip):
                best = polished
        except Exception:
            pass

    dist, dur = leg_totals(best, data.distance_matrix, matrix, round_trip=data.round_trip)
    return AlgorithmOutput(
        order=best,
        total_duration_s=dur,
        total_distance_m=dist,
        meta=META,
        notes=(
            "Realized-cost ALNS with drift-segment destroy, profile-aware regret repair, "
            f"and {NOMINAL_EPSILON:.0%} nominal slack on incumbent updates."
        ),
    )
