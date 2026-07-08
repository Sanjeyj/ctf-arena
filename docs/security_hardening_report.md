# Security Hardening Report (v1.0.0-rc1)

## Executive Summary

This report reviews the security posture, defensive controls, input sanitization, and data integrity mechanisms implemented in the Cyber Defense Platform (CDP).

---

## Authentication & Authorization Hardening

### 1. JWT Authentication (API endpoints)
- **Token Validation**: Signature verification uses HS256 algorithm with application `SECRET_KEY`.
- **Expiration Enforcement**: Tokens require `exp` claim. Expired tokens are rejected with a `401 Unauthorized` response.
- **Malformed & Missing Tokens**: Handled gracefully. If `Authorization` header is missing, malformed, or signature is invalid, request is blocked.

### 2. RBAC & Access Control
- **Role Verification**: Admin views are protected by `@require_admin` wrapper which verifies active sessions and role-type membership.
- **Resource Ownership**: Scoped querying ensures that tenant users cannot list, view, edit, or delete other tenant's resources.

---

## Input Handling & Validation

### 1. JSON Validation & Parser Safety
- All API POST handlers validate request payloads.
- JSON structure parsing failures (e.g. malformed JSON strings) are handled at Flask request parser level, returning `400 Bad Request`.

### 2. Numeric and Enum Clamping
- **Score Limits**: Platform readiness and certification metrics validate or clamp scores to the `[0.0, 100.0]` range.
- **Appetite Check**: Risk appetite scores are validated.
- **Status Choice Constraints**: All stateful models (e.g. ADRs, Certifications, Simulations) validate that inputs belong to predefined choices (`draft`, `active`, `proposed`, `accepted`, `completed`, `failed`).

---

## AI Safety & Prompt Injection Defenses

The `ExecutivePlatformAI` service implements multi-layered safety controls:

### 1. Prompt Injection Detection (7 patterns)
All prompts sent to the executive AI service are passed through sanitizers looking for keywords and patterns:
- Instruction overrides (e.g. `ignore previous instructions`, `forget rules`)
- Output format modifiers (e.g. `print the flag`, `reveal flag`)
- Jailbreaks (e.g. `dan mode`, `jailbreak mode`)
- System prompt manipulation attempts

Detection of these patterns raises `ValueError` and halts execution.

### 2. Output Secret Masking
To prevent the leakage of sensitive data through LLM outputs, the service applies string regex redaction filters:
- **CTF Flags**: Redacts standard flag formats (e.g., `CTF{...}` -> `[CTF_FLAG_REDACTED]`).
- **Authorization Tokens**: Redacts JWT/Bearer patterns (e.g., `Bearer <token>` -> `Bearer [REDACTED]`).
- **Secrets/Passwords**: Masks API keys, system passwords, and common credential shapes.

---

## Data Integrity Invariants

1. **Deterministic Release Hashes**:
   - `ReleaseBaselineService` generates a SHA-256 hash by dumping metrics into JSON with sorted keys. This ensures identical inputs produce identical hashes, enabling tamper-evident release verification.
2. **Deterministic Simulations**:
   - Random seeds are enforced for all stochastic simulations (such as Monte Carlo risk simulations and contagion propagations) to guarantee reproducibility.
3. **FSM Enforcement (ADRs)**:
   - Architecture Decision Records enforce valid state transitions:
     - `proposed` -> `accepted` or `deprecated`
     - `accepted` -> `deprecated` or `superseded`
     - All invalid state transitions raise `ValueError` and are rejected.
4. **Mandatory Human Signature**:
   - All release baselines, release gates, and ADR approvals require an explicit `approved_by` signature. Auto-population of approvals is prohibited.
5. **Self-Edge & Duplicate Protection**:
   - Capability registry prevents self-edges (capability depending on itself) and duplicate edges in dependency graphs.
