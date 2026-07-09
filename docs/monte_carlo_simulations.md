# Monte Carlo Loss Simulations Guide

This guide details the Monte Carlo methodology used to calculate cyber risk exposures.

## Simulation Details

- **Distribution Models**: Supports Triangular and Beta-PERT probability density samplers for annual incident rates and incident losses.
- **Pseudo-Random Reproducibility**: Uses explicit random seeds during trials to ensure deterministic reproducibility in test suites.
- **Offline Limits**: Runs local simulations only; maximum iteration counts are capped at 100,000.
