# Contagion Propagation Simulation Guide

This document describes the simulation-only contagion propagation engine.

## Propagation Algorithm
All contagion runs are strictly **offline** and **simulation-only**. No live network scanning or cloud resource mutation is permitted:
- **Queue-based BFS traversal** propagates failure starting from a defined `initial_node_id`.
- **Cycle protection** prevents infinte loops.
- **Propagation Depth Limit** bounds traversal hops to avoid performance exhaustion.

## Seed-Based Determinism
Each `ContagionScenario` has a configured `random_seed`. Using this seed, a pseudorandom number generator produces identical, reproducible outputs for subsequent simulation replays.
- Clamps effective propagation probability within `[0.0, 1.0]`.
- Resilience absorption factor reduces impact scores, clamping scores within `[0.0, 100.0]`.
