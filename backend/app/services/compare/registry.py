"""Compare provider registry."""

from __future__ import annotations

from typing import Awaitable, Callable

from app.config import Settings
from app.services.compare.base import CompareInput, CompareOutput, ProviderMeta

from . import (
    apple_maps_manual,
    google_maps_manual,
    mapbox_optimization,
    nn_2opt_matrix,
    openrouteservice,
    ortools_gls_matrix,
    route_optimizer_dcir,
)

CompareRunner = Callable[[CompareInput, Settings], Awaitable[CompareOutput]]

_REGISTRY: dict[str, tuple[ProviderMeta, CompareRunner]] = {}


def _register(module) -> None:
    _REGISTRY[module.META.id] = (module.META, module.compare)


for _mod in (
    route_optimizer_dcir,
    ortools_gls_matrix,
    nn_2opt_matrix,
    mapbox_optimization,
    openrouteservice,
    google_maps_manual,
    apple_maps_manual,
):
    _register(_mod)


def list_providers() -> list[ProviderMeta]:
    return [meta for meta, _ in _REGISTRY.values()]


async def run_provider(provider_id: str, data: CompareInput, settings: Settings) -> CompareOutput:
    if provider_id not in _REGISTRY:
        raise KeyError(f"Unknown compare provider: {provider_id}")
    _, runner = _REGISTRY[provider_id]
    return await runner(data, settings)


async def run_all_providers(data: CompareInput, settings: Settings) -> list[CompareOutput]:
    import asyncio

    tasks = [runner(data, settings) for _, runner in _REGISTRY.values()]
    return list(await asyncio.gather(*tasks))
