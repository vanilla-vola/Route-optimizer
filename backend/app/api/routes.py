from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.core.exceptions import MatrixError, OptimizationError
from app.models.schemas import OptimizeRequest, OptimizeResponse, PlaceSuggestion
from app.models.transport_modes import TRANSPORT_MODE_CATALOG
from app.services.coordinates import to_mapbox_coords
from app.services.matrix import build_matrix
from app.services.dcir import LegRefreshConfig, solve_dcir_hybrid
from app.services.matrix_profiles import build_matrix_bundle
from app.services.optimizer import solve_route
from app.services.profiles import build_profile_matrices
from app.services.geocoding import enrich_stop_names, reverse_geocode, search_places
from app.services.route_builder import build_optimize_response

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/transport-modes")
async def transport_modes() -> list[dict]:
    """Mapbox-supported matrix profiles exposed to clients."""
    return [mode.model_dump() for mode in TRANSPORT_MODE_CATALOG]


@router.get("/search-places", response_model=list[PlaceSuggestion])
async def search_places_endpoint(
    q: str,
    limit: int = 6,
    settings: Settings = Depends(get_settings),
) -> list[PlaceSuggestion]:
    """Search places by name or address (Mapbox, then free Nominatim fallback)."""
    return await search_places(q, settings=settings, limit=limit)


@router.get("/reverse-geocode")
async def reverse_geocode_endpoint(
    lat: float,
    lng: float,
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """Resolve lat/lng to a place name (Mapbox, then free Nominatim fallback)."""
    name = await reverse_geocode(lat, lng, settings=settings)
    return {"name": name}


@router.post("/optimize-route", response_model=OptimizeResponse)
async def optimize_route(
    request: OptimizeRequest,
    settings: Settings = Depends(get_settings),
) -> OptimizeResponse:
    if len(request.stops) > settings.max_stops:
        raise HTTPException(
            status_code=400,
            detail=f"At most {settings.max_stops} stops are supported (Mapbox matrix limit).",
        )

    coords = to_mapbox_coords(
        [{"lat": stop.lat, "lng": stop.lng} for stop in request.stops],
    )
    profile = request.mode or settings.matrix_profile

    profile_source: Optional[str] = None
    profile_matrices = None
    try:
        distances, durations = await build_matrix(
            coords,
            settings=settings,
            profile=profile,
        )
        if settings.use_dcir:
            bundle = await build_matrix_bundle(
                coords,
                settings=settings,
                profile=profile,
                base_distances=distances,
                base_durations=durations,
            )
            distances = bundle.distances
            durations = bundle.durations
            profile_source = bundle.profile_source
            profile_matrices = bundle.profile_matrices

            leg_refresh = None
            if settings.dcir_refresh_legs and settings.mapbox_access_token:
                leg_refresh = LegRefreshConfig(
                    coords=tuple(coords),
                    settings=settings,
                    profile=profile,
                    timezone=settings.dcir_timezone,
                )

            order, _ = await solve_dcir_hybrid(
                durations,
                profile_matrices=bundle.profile_matrices,
                start_fixed=request.start_fixed,
                end_fixed=request.end_fixed,
                round_trip=request.round_trip,
                time_limit_s=settings.dcir_time_limit_s,
                robust_lambda=settings.dcir_robust_lambda,
                leg_refresh=leg_refresh,
            )
            solver_name = "dcir-hybrid"
        else:
            order, _ = solve_route(
                durations,
                start_fixed=request.start_fixed,
                end_fixed=request.end_fixed,
                round_trip=request.round_trip,
                time_limit_s=settings.solver_time_limit_s,
            )
            solver_name = "ortools-gls"
            profile_matrices = build_profile_matrices(durations)
    except MatrixError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except OptimizationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    stops = await enrich_stop_names(request.stops, settings=settings)

    return build_optimize_response(
        order,
        stops,
        distances,
        durations,
        round_trip=request.round_trip,
        mode=profile,
        solver=solver_name,
        profile_source=profile_source if settings.use_dcir else "synthetic",
        profile_matrices=profile_matrices,
    )
