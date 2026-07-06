# AI Model Governance Guide

AI Model Governance enforces model risk catalog registries, model safety benchmarks reviews, and lifecycle audits.

## Model Lifecycle

AI records transition through standard states:
- `draft`: Initial review staging.
- `evaluation`: Benchmark runs checking prompt safety.
- `approved`: Allowed for wargames and simulation calls.
- `restricted`: Blocked due to safety score drops.
- `retired`: Retired from the library.

## Evaluation & Benchmarks

Integrates safety sanitization, flag-redaction, and injection filtering before prompting model endpoints.
