# Incident Metrics & KPIs
# CTF Arena v1.0.0 — EthicBids Technologies™

This document defines the key performance indicators (KPIs) used to evaluate operational health and incident response effectiveness.

---

## 1. Core KPIs

Operators must track and report these KPIs quarterly:

### A. Mean Time To Detect (MTTD)
The average time from the start of an incident to its identification by automated monitoring or manual report:
$$\text{MTTD} = \frac{\sum (\text{Time Detected} - \text{Time Started})}{\text{Total Incident Count}}$$
* **Target**: **< 5 Minutes** for P1 incidents.

### B. Mean Time To Resolve (MTTR)
The average time from identification of an incident to system recovery:
$$\text{MTTR} = \frac{\sum (\text{Time Resolved} - \text{Time Detected})}{\text{Total Incident Count}}$$
* **Target**: **< 2 Hours** for P1 incidents.

### C. Mean Time Between Failures (MTBF)
The average uptime elapsed between system failures:
$$\text{MTBF} = \frac{\text{Total Uptime}}{\text{Total Failure Count}}$$
* **Target**: **> 90 Days**.

---

## 2. Reporting & Post-Mortem Cadence

- Every P1 or P2 incident requires a mandatory post-mortem review within **48 hours** of resolution.
- Quarterly review reports must aggregate the MTTD, MTTR, and MTBF metrics to highlight infrastructure areas requiring architectural enhancement or capacity scaling.
