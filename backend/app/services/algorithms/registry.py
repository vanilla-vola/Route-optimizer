"""Algorithm plugin registry."""

from __future__ import annotations

from typing import Awaitable, Callable

from app.services.algorithms.base import AlgorithmInput, AlgorithmMeta, AlgorithmOutput

from . import (
    alns,
    christofides_gls,
    dcir_hybrid,
    drpt_alns,
    input_order_baseline,
    learning_augmented_insertion,
    multi_start_gls,
    nn_2opt,
    ortools_gls,
    parallel_insertion_gls,
    pda_alns,
    popmusic_gls,
    regret_2_insertion,
    savings_gls,
    simulated_annealing,
    td_alns_rrd,
    tunesearch_warmstart_gls,
)

AlgorithmRunner = Callable[[AlgorithmInput], Awaitable[AlgorithmOutput]]

_REGISTRY: dict[str, tuple[AlgorithmMeta, AlgorithmRunner]] = {}


def _register(module) -> None:
    _REGISTRY[module.META.id] = (module.META, module.run)


for _mod in (
    drpt_alns,
    dcir_hybrid,
    pda_alns,
    ortools_gls,
    christofides_gls,
    savings_gls,
    parallel_insertion_gls,
    nn_2opt,
    regret_2_insertion,
    alns,
    popmusic_gls,
    multi_start_gls,
    td_alns_rrd,
    tunesearch_warmstart_gls,
    learning_augmented_insertion,
    simulated_annealing,
    input_order_baseline,
):
    _register(_mod)


def list_algorithms() -> list[AlgorithmMeta]:
    return [meta for meta, _ in _REGISTRY.values()]


def get_algorithm(algorithm_id: str) -> tuple[AlgorithmMeta, AlgorithmRunner]:
    if algorithm_id not in _REGISTRY:
        raise KeyError(f"Unknown algorithm: {algorithm_id}")
    return _REGISTRY[algorithm_id]


async def run_algorithm(algorithm_id: str, data: AlgorithmInput) -> AlgorithmOutput:
    _, runner = get_algorithm(algorithm_id)
    return await runner(data)
