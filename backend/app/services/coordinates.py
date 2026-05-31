def to_mapbox_coords(stops: list[dict]) -> list[tuple[float, float]]:
    """Convert lat/lng dicts to Mapbox (lng, lat) tuples."""
    return [(stop["lng"], stop["lat"]) for stop in stops]
