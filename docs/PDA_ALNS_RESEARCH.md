# PDA-ALNS: Profile-Drift Adaptive Large Neighborhood Search

IEEE-oriented algorithm (`pda-alns`) for departure-consistent multi-stop routing.

## Problem

Static TSP solvers minimize one duration matrix. In traffic-aware routing, **realized** tour time depends on **when** each leg departs (off-peak / nominal / peak profiles). A tour that is optimal on the nominal matrix can be suboptimal under forward simulation.

## Method (implemented in `backend/app/services/algorithms/pda_alns.py`)

| Component | Description |
|-----------|-------------|
| **Destroy — drift segment** | Uses `refreshed_leg_costs` to find legs where profile-at-departure cost diverges >15% from nominal; removes a contiguous block of stops on those legs. |
| **Destroy — random** | Diversification (ALNS-style). |
| **Repair — profile-aware regret-2** | Reinserts removed stops using regret insertion with the profile matrix active at simulated departure time. |
| **Repair — segment OR-Tools** | Re-optimizes drifted segment via `solve_segment` (same idea as DCIR Phase 3). |
| **Acceptance** | Primary objective: **realized** duration (`tour_cost_breakdown`). Incumbent updates require nominal within **1%** of best nominal (ε-constraint, aligned with DCIR Phase 2). |
| **Polish** | Optional final OR-Tools GLS if time remains. |

## Comparison to DCIR-Hybrid

| | DCIR-Hybrid | PDA-ALNS |
|---|-------------|----------|
| Structure | Fixed 5-phase pipeline | Adaptive ALNS loop |
| Destroy criterion | Drift → segment repair | Drift + random + weighted selection |
| Objective emphasis | Nominal first, robust tie-break | **Realized-first** with nominal ε |
| Novelty for paper | System integration | **Drift-guided ALNS operators** |

## Evaluation protocol (use existing API)

1. Enable Mapbox profiles: `DCIR_MAPBOX_PROFILES=true`, `driving-traffic`, 7–12 stops.
2. `POST /benchmark-algorithms` with `time_limit_s=12`.
3. Compare **realized_duration_s** for `pda-alns` vs `dcir-hybrid`, `alns`, `td-alns-rrd`, `ortools-gls`.
4. Ablation: disable operators in code or run subsets via future flags.

## Suggested paper title

*Profile-Drift Adaptive Large Neighborhood Search for Departure-Consistent Multi-Stop Routing Under Multi-Layer Traffic Matrices*

## Next steps for IEEE submission

- [ ] 30–50 urban instances (JSON coordinates in `benchmarks/instances/`)
- [ ] Batch runner script + CSV results
- [ ] Wilcoxon signed-rank vs OR-Tools GLS on realized time
- [ ] Ablation table: drift-only, regret-only, full PDA-ALNS
