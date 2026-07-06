# Strategic Operations Guide

The **Strategic Operations** layer handles high-level mission goals, alignment milestones, and national cyber defense campaign coordination.

## Components

- **Strategic Objective:** Concrete cyber objectives with priorities ranging from Critical (1) to Low (5).
- **Threat Campaign Global:** Real-time threat campaigns mapped by region, impact, and prediction confidence.

## Service Functions

- `prioritize(org_id)`: Sorts open and in-progress objectives from high to low priority.
- `evaluate(objective_id)`: Returns health metrics (`on_track` or `at_risk`).
- `report(org_id)`: Aggregates counts and average progress percentage.
