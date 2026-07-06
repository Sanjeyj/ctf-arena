# Posture Fusion Engine Guide

The **Posture Fusion Engine** aggregates security parameters across SOC detections, cloud mesh routes, compliance logs, and commander readiness status.

## Domain Aggregation

Calculates health index across registered domains:
$$\text{Global Readiness} = \frac{\text{Domain Health} + \text{Domain Readiness} + \text{Resilience Score}}{3}$$

## Missing Subsystem Data

If a domain has no active telemetry, it degrades gracefully to default scores, ensuring full system stability.

## Trend Historical Metrics

Metrics are captured and logged to the `UniverseMetric` table for historical line graphs.
