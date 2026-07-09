# Federated Governance Guide

This document describes the federated governance decision ledger.

## Governance Records
Tracks proposed changes to collective cyber resilience policies:
- Types include: `collective_control`, `dependency_diversification`, `shared_recovery`, `mutual_aid_policy`, `sector_priority`, `systemic_risk_acceptance`, `collective_investment`.
- Computes support, opposition, and consensus scores based on simulated participant votes.

## State Transitions & Human Approval
Enforces strict lifecycle state transitions (`proposed` -> `reviewing` -> `approved`/`rejected`). Transitioning a proposal to an approved decision requires explicit human signature (`approved_by`).
- Ensures rejected proposals cannot be silently approved.
- Systemic risk impacts are recorded and validated within `[-100.0, 100.0]`.
