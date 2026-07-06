# Zero Trust Assurance Guide

This module explains simulated identity trust evaluation and device security posture calculations.

## Identity Trust scoring formula

$$\text{Identity Trust} = (\text{Authentication Strength} \times 100) - (\text{Risk Score} \times 50)$$

If identity status is restricted, it caps the score at 40.0. If revoked, it sets the score to 0.

## Device Posture scoring formula

$$\text{Posture} = (\text{Patch Score} \times 50) + (50 \text{ if encryption enabled}) - (\text{Endpoint Protection Penalty})$$

## Zero Trust Decision Matrix

Combined score weighting:
- Identity Trust: 40%
- Device Posture: 30%
- Policy Compliance: 20%
- Resource Sensitivity: 10%

Decision Threshold Boundaries:
- Score >= 80: `allow`
- 60 <= Score < 80: `allow_with_monitoring`
- 40 <= Score < 60: `require_step_up`
- Score < 40: `deny_simulation`
