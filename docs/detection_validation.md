# Detection Validation & Signal Emulation

Detection Validation assesses Sigma rules, YARA rules, IOC matches, and correlation models using synthetic signal verification.

## Architecture & Mechanics

1. **Synthetic Signals Generation**: Synthesizes event signatures for simulated detection inputs.
2. **Coverage scoring**: Calculates overall coverage ratio as the ratio of rules that successfully trigger over total expected rules.
3. **Latency scoring**: Penalizes slower detection delays based on:
   $$LatencyScore = \max(0.0, 1.0 - \frac{LatencySeconds}{300})$$
4. **Gap Analysis**: Identifies rule sets that failed to trigger despite expectation, pinpointing areas where log pipelines or rules need tuning.
