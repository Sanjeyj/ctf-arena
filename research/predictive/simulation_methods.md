# Monte Carlo Simulation Methods — CDP v2.0

## 1. Monte Carlo Loss Iterations

The predictive engine runs Monte Carlo simulations to estimate potential annual financial losses from security incidents:

```
[Simulation Parameters] ──> [Generate Random Loss Events] ──> [Iterate 10,000 runs] ──> [Loss Exceedance Curve]
```

---

## 2. Parameter Modeling (PERT Distribution)

Loss occurrences use the Beta-PERT distribution to model probability ranges:

- **Minimum Loss ($L_{min}$)**: Ideal case with zero lateral movement and immediate containment.
- **Most Likely Loss ($L_{mode}$)**: Normal containment path with minor node compromise.
- **Maximum Loss ($L_{max}$)**: Worst case scenario with propagation across critical nodes.
- **Calculation**: Generates loss event variables for 10,000 iterations to output annual loss exceedance curves.
