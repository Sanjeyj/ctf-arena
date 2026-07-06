# Defense Universe Guide

The **Unified Cyber Defense Universe** is the central container model that connects GRC policies, SIEM/SOC response plans, LMS trainings, and wargaming simulations into a single logical model.

## Universe Lifecycle

A universe exists in one of the following states:
1. `draft`: Inactive sandbox environment.
2. `active`: Active and receiving aggregated scores updates.
3. `paused`: Temporarily halted measurements.
4. `completed`: Read-only historical run.
5. `archived`: Soft-deleted.

## Domain & Topology Mapping

A universe is divided into logical **Domains** (e.g. SOC, Cloud, LMS). Within each domain, **Nodes** represent logical infrastructure components linked by **UniverseLinks** specifying trust and dependency weights.

## Topology API

- Retrieve topological structures via `GET /api/v1/universe/<id>/topology`.
