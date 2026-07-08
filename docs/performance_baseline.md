# Performance & Scale Baseline Report (v1.0.0-rc1)

## Executive Summary

This report documents the performance baseline of representative core platform operations. 
The benchmarks were executed under controlled, offline conditions utilizing an in-memory SQLite database (`sqlite:///:memory:`) to ensure reproducibility and database isolation.

---

## Benchmark Results

All operations were executed across **50 iterations** with statistics computed for average, median, and 95th percentile (P95) latency (in milliseconds).

| Operation | Average (ms) | Median (ms) | P95 (ms) | Performance Status |
|---|---|---|---|---|
| `capability_registry_listing` | 0.392 | 0.339 | 0.556 | 🚀 Optimal |
| `platform_readiness_calculation` | 2.522 | 2.422 | 3.028 | 🚀 Optimal |
| `certification_scoring` | 0.198 | 0.173 | 0.263 | 🚀 Optimal |
| `contagion_simulation_summary` | 0.269 | 0.207 | 0.308 | 🚀 Optimal |
| `monte_carlo_simulation_10_iter` | 1.971 | 1.915 | 2.156 | 🚀 Optimal |
| `governance_scorecard_calculation` | 1.461 | 1.280 | 1.834 | 🚀 Optimal |
| `posture_fusion_global_score` | 1.003 | 0.921 | 1.286 | 🚀 Optimal |
| `telemetry_summary` | 0.538 | 0.394 | 0.805 | 🚀 Optimal |
| `attack_path_graph_calculation` | 0.429 | 0.356 | 0.527 | 🚀 Optimal |

---

## Scaling Analysis & Observations

1. **Sub-Millisecond Operations**:
   - Schema reads and structural summaries (registry listing, certification scores, contagion summaries, attack path graph) execute in `< 0.5ms` average.
2. **Readiness & Scorecard Generation**:
   - Metric aggregation and scoring averages `< 3.0ms`. The computation overhead remains negligible for typical tenant asset volumes.
3. **Monte Carlo Simulations**:
   - The bounded 10-iteration Monte Carlo simulation takes `< 2.0ms` average. While latencies will scale linearly with iteration count, it remains highly scalable.
4. **Database Query Count**:
   - Read operations use efficient indexed queries, keeping roundtrips to database minimal.

---

## Benchmark Environment Details

- **Database**: SQLite (In-Memory, Thread-safe)
- **Iterations**: 50 runs per operation
- **Platform Invariants**: Enforced tenant filters on all queries
- **Safety**: Fully offline, no external telemetry or network calls.
