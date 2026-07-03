# Security Economy Engine Guide

## Overview

The Security Economy Engine tracks cybersecurity investments, annual compounding growth projections, market values, and national cybersecurity workforce credentials.

---

## Economic Profiles

Economic stats are logged via `SecurityEconomy`:
*   `investment` — Accumulated investment ledger total.
*   `growth_rate` — Annual projected economic compound growth rate.
*   `workforce_score` — Combined workforce skill index.
*   `market_value` — Cumulative simulated valuation metric.

---

## Security Workforce Profiles

Credentials and roles are modeled in `WorkforceProfile`:

- `role` — Title of the workforce profile (`Analyst`, `Architect`, `Developer`, `Lead`)
- `skill_score` — Competency indicator score `[0.0, 1.0]`
- `experience` — Professional experience track (years)
- `certifications` — Certifications achieved

---

## Economic API

```python
# Record economic investment
econ = EconomyService.investment(amount=500000.0, org_id=1)

# Project growth rate
growth = EconomyService.growth(org_id=1)

# Retrieve workforce status summary
workforce_info = EconomyService.workforce(org_id=1)
# Returns: {'total_workforce': 12, 'avg_skill': 0.825, 'capacity': 'high'}
```
