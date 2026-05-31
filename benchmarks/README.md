# Benchmark instances (IEEE-style suite)

Forty fixed **vehicle routing** instances for reproducible experiments across Indian metros. Each instance defines real coordinates, `driving-traffic` mode, and round-trip depot semantics.

## Files

| Path | Purpose |
|------|---------|
| `instances/manifest.json` | Summaries (id, city, pattern, stop count, description) |
| `instances/<id>.json` | Full stop list + metadata |
| `instances_catalog.json` | Copy of manifest + embedded payloads for offline scripts |

## Patterns (diversity for papers)

- **Cross-city / span** — long geographic spread (e.g. Mumbai cross, Delhi NCR)
- **Ring / outer** — perimeter tours (Bangalore outer, Pune ring)
- **Corridor / ORR / OMR** — linear high-traffic axes (Hyderabad ORR, Chennai OMR)
- **Airport / hub** — airport-adjacent and logistics hubs
- **Peak / mixed** — dense CBD + suburban mixes for profile drift stress tests

Stop counts range from **6–12** stops per instance.

## API (backend)

- `GET /benchmark-instances` — list summaries
- `GET /benchmark-instances/{instance_id}` — full detail

Run the API from the **repository root** (or ensure `benchmarks/instances/manifest.json` is reachable). Docker images must copy the `benchmarks/` folder if you serve instances from a container.

## Web & mobile UI

- **Instance** dropdown (left of **Algorithm**): pick an instance, hover **View stops** for coordinates, **Load this instance**, then run Optimize / Benchmark / Compare.
- Regenerate: `python scripts/generate_benchmark_instances.py`

## Batch experiments

```bash
python scripts/run_benchmark_batch.py --instances-dir benchmarks/instances
```

Use `DCIR_MAPBOX_PROFILES=true` and a valid `MAPBOX_ACCESS_TOKEN` for profile-aware (nominal vs realized) metrics.
