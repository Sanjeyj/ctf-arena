# Security Assurance Cases Claims Guide

Structured Claims evaluation aggregates linked compliance evidence to compute overall wargaming verification confidence indices.

## Confidence score logic

- Every supporting link adds its weight component:
  - `supports`: weight * 100
  - `compensating_control`: weight * 80
- If any contradictions are linked with type `contradicts`, the entire confidence score faces an 80% penalty multiplier (retains only 20% of calculated confidence).
- Scope checks ensure cross-tenant evidence is rejected.
