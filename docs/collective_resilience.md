# Collective Resilience & Mutual Aid Guide

This document covers collective resilience planning and simulated capacity allocation.

## Resilience Planning
* **Baseline Scores**: The average resilience score across all participating nodes.
* **Target Scores**: The estimated improvement target based on a specified improvement factor.
* **Risk Reduction**: Estimated systemic risk reduction percentage achieved by implementing the plan.

## Mutual Aid Capacity Allocation
Simulates mutual-aid capacity matching between a provider node and a recipient node affected by a contagion simulation:
- Clamps capacity allocation below the provider's available capacity.
- Evaluates recovery gain score.
- **Human Approval Requirement**: Requires explicit human action to transition status from `pending` to `approved` or `allocated_simulation`.
