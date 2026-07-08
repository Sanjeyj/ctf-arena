# AI Safety Incident Runbook

**Purpose**: Procedure for investigating and responding to AI safety incidents, including prompt injection attempts and sensitive data leakage through AI outputs.  
**Platform AI Components**: `ExecutivePlatformAI`, `ExecutiveSystemicRiskAI`, `ExecutiveGovernanceAI`, `ExecutiveStrategyAI`, `ExecutiveRiskAI`, `ExecutiveValidationAI`, `ExecutiveExposureAI`, `ExecutiveAssuranceAI`, `ExecutiveControlAI`, `ExecutiveUniverseAI`, `ExecutiveReliabilityAI`

---

## Prerequisites

- Access to application logs (`logs/app.log`, `logs/error.log`)
- Admin access to the platform
- No direct access to external AI provider credentials required (all calls are to `AIService` which uses `StubProvider` in current configuration)

---

## Detection Signals

An AI safety incident may be indicated by:

1. `ValueError` in logs from any `Executive*AI` service mentioning "prompt injection"
2. AI output containing patterns like `CTF{`, `Bearer `, `password=`, `api_key=`
3. User-reported AI responses containing sensitive data
4. Unexpected AI output format (e.g., base64 blobs, JSON payloads)

---

## Triage Procedure

### Step 1 — Identify the Triggering Request

Search logs for the incident timestamp:

```bash
Select-String "prompt injection\|REDACTED\|ExecutiveAI" logs/app.log | Select-Object -Last 20
```

### Step 2 — Review the Prompt Input

> **⚠ Do NOT log or display raw prompt inputs that may contain sensitive data.**

Identify:
- Which briefing method was called (e.g., `generate_readiness_briefing`)
- Which `organization_id` triggered the call
- Whether the input contained injected keywords

### Step 3 — Verify Masking Worked

Check if the output was masked:
- CTF flags: `CTF{...}` → `[CTF_FLAG_REDACTED]`
- Bearer tokens: `Bearer <token>` → `Bearer [REDACTED]`
- Passwords/API keys: `[SECRET_REDACTED]`

If masking did NOT work, this is a **Priority 1 incident**.

### Step 4 — Block the User/Tenant (if applicable)

If a deliberate prompt injection attack is identified:
- Temporarily disable the `organization_id` in question via admin panel
- Revoke the associated JWT tokens by rotating the `SECRET_KEY`

### Step 5 — Review and Update Injection Detection Patterns

Current patterns checked (in all Executive AI services):
- `ignore previous instructions`
- `forget your rules`
- `print the flag`
- `reveal flag`
- `dan mode`
- `jailbreak`
- `ignore all instructions`

If a new bypass pattern is discovered, add it to all `Executive*AI` service classes and run the full test suite.

---

## Governance Rule

> AI output masking and prompt injection detection must NEVER be weakened or disabled. Any modification to detection patterns requires a security review and full test regression.

---

## Escalation Condition

Escalate immediately to security team if:
- AI output contains unmasked secrets
- A novel jailbreak pattern bypasses all 7 detection checks
- The `StubProvider` is replaced with a live LLM without security review

---

## Audit Evidence to Retain

- Log excerpt showing the injection attempt and `ValueError` raised
- Organization ID of the triggering tenant
- Briefing method name
- Timestamp of detection
- Any changes made to injection detection patterns
- Commit reference for any fix
