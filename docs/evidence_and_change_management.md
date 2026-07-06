# Evidence & Change Management Guide

This module manages secure compliance hashes cataloging and configuration change requests tracking.

## Compliance Evidence

- **Integrity:** Verification checks use SHA-256 hashes generated over canonicalized resource values.
- **Redaction:** Secrets, bearer tokens, API keys, passwords, and CTF flag headers are redacted prior to hashing.

## Configuration Change Lifecycle

Changes undergo state transitions within a safe simulated sandbox:
1. `requested`
2. `reviewed` (risk score assessed)
3. `approved`
4. `simulated`
5. `completed`
6. `rolled_back` (if simulation alerts trigger)
