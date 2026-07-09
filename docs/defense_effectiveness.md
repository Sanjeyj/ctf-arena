# Defense Effectiveness Metrics & Posture Analysis

The Defense Effectiveness Fabric calculates continuous posture health metrics to give executives a centralized indicator of security strength.

## Composite Score Model

The composite index is computed as a weighted score across five pillars:
1. **Control Effectiveness (25%)**: Performance score of compliance/operational controls.
2. **Detection Validation (25%)**: Average rule triggers and latency scores.
3. **Playbook Readiness (20%)**: Structural correctness, dependency checks, and evidence ratings.
4. **Resilience Engineering (15%)**: System recovery and chaos exercise ratings.
5. **Architecture Zones (15%)**: Boundary violations and segmentation strength.

$$CompositeScore = 0.25 \times Ctrl + 0.25 \times Det + 0.20 \times Play + 0.15 \times Res + 0.15 \times Arch$$

Trend calculations analyze relative deltas across runs to determine if the posture is `improving`, `stable`, or `declining`.
