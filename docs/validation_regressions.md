# Validation Regressions & Risk Management

Validation regressions identify performance drops in platform controls, detections, or playbooks compared to their previous baselines.

## Severity Classification

A regression is triggered when a baseline validation score drops, and is classified as follows:
- **Delta < 5**: No regression triggered.
- **Delta 5 - 10**: Low severity regression.
- **Delta 10 - 20**: Medium severity regression.
- **Delta 20 - 30**: High severity regression.
- **Delta >= 30**: Critical severity regression.

## Resolution Workflow

1. **Detection**: Run automated evaluations to detect regressions.
2. **Investigation**: Regressions are logged in an `open` status for security response teams.
3. **Resolution**: Remediation plans map compensating controls to resolve the gap, and the regression record is marked `resolved`.
