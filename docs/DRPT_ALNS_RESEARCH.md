# DRPT-ALNS: Distributionally Robust Pareto-Temporal ALNS

`drpt-alns` is the strongest research-oriented algorithm currently in this repository. It is designed as a clearer IEEE-level contribution than DCIR-Hybrid or PDA-ALNS because it changes the search objective from a single scalar route score to a Pareto and distributionally robust traffic objective.

## Core Research Claim

Most route optimizers rank tours by a single nominal matrix, and many traffic-aware heuristics optimize a single realized simulation. DRPT-ALNS instead maintains a Pareto archive over five criteria:

| Criterion | Meaning |
|---|---|
| Nominal duration | Static matrix duration, comparable to conventional TSP solvers |
| Realized duration | Departure-consistent forward simulation |
| Worst-profile duration | Adversarial cost if one traffic profile dominates |
| CVaR-tail duration | Mean of the upper tail of profile costs |
| Drift exposure | Total planned-vs-active-profile leg mismatch |

The final route is selected by a robust score within a small nominal slack. This makes the algorithm suitable for the claim: **robust multi-stop routing under traffic-profile uncertainty**.

## Algorithmic Components

1. **Multi-seed initialization:** OR-Tools strategies, NN+2-opt, and regret insertion.
2. **Pareto archive:** Stores only non-dominated tours over the five criteria.
3. **Adversarial-tail destroy:** Removes stops around legs with high active-profile, worst-profile, or drift cost.
4. **Pareto-guided destroy:** Compares the current tour with archive elites and removes stops with high positional disagreement.
5. **Pareto regret repair:** Re-inserts removed stops using profile-active insertion costs.
6. **Segment polish:** Re-optimizes drifted segments with OR-Tools when appropriate.
7. **Distributionally robust selection:** Selects final tour using realized + CVaR + worst-profile + drift penalty under nominal slack.

## Why This Is More Original Than DCIR/PDA-ALNS

| Algorithm | Main idea | Research weakness | DRPT-ALNS improvement |
|---|---|---|---|
| DCIR-Hybrid | Fixed phased pipeline | Mostly orchestration of known methods | Uses multi-objective Pareto search |
| PDA-ALNS | Drift-guided ALNS | Single archive-free objective | Adds distributional robustness and non-dominated archive |
| T-ALNS-RRD baseline | Peak-cost destroy | Targets peak cost only | Targets active, worst, CVaR, and drift exposure jointly |

## Required Experiments for IEEE

Minimum acceptable study:

- 30-50 urban instances, 7-15 stops each.
- `driving-traffic`, `DCIR_MAPBOX_PROFILES=true`.
- Baselines: `dcir-hybrid`, `pda-alns`, `ortools-gls`, `alns`, `td-alns-rrd`, `nn-2opt`.
- Metrics: nominal, realized, worst-profile, CVaR-tail, drift exposure.
- Statistical test: Wilcoxon signed-rank on realized duration and robust score.
- Ablation: remove adversarial-tail destroy, remove Pareto-guided destroy, remove CVaR term.

## Suggested IEEE Paper Title

**Distributionally Robust Pareto-Temporal Adaptive Large Neighborhood Search for Multi-Stop Routing Under Traffic-Profile Uncertainty**

## Honest Scope

This is not a mathematical proof of optimality. Its publishability depends on strong empirical evidence that Pareto robust search improves realized or tail-risk performance over DCIR, ALNS, and T-ALNS-style baselines. If those wins do not appear on Mapbox-profile instances, the algorithm should be framed as a negative or systems result rather than a breakthrough.
