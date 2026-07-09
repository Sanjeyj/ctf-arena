# Security Portfolio Budget Optimization

This document outlines budget-constrained portfolio optimization logic.

## Knapsack Solver

- **Objective**: Maximize combined risk reduction + expected resilience gain.
- **Constraints**: Sum of allocated budgets for selected options cannot exceed total budget limit.
- **Implementation**: Runs deterministic offline greedy knapsack algorithms using priority rankings.
