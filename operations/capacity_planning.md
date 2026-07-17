# Capacity Planning & Resource Scaling
# CTF Arena v1.0.0 — EthicBids Technologies™

This document outlines the resource metrics, scale-up thresholds, and hardware recommendations for CTF Arena v1.0.0 deployments.

---

## 1. Resource Utilization Thresholds

To prevent capacity exhaustion, trigger scaling reviews when utilization meets these limits:

| Resource | Scale-Up Threshold | Action Required |
|----------|--------------------|-----------------|
| **CPU Utilization** | > 70% sustained for 15 mins | Horizontal scale (add Gunicorn workers or app replicas) |
| **Memory Utilization** | > 80% sustained | Vertical scale (increase container RAM allocation) |
| **Disk Space (Uploads)** | > 75% utilized | Expand persistent volume or move uploads to object storage |
| **Postgres Connections** | > 80% pool usage | Upgrade database class or increase connection pool limit |

---

## 2. Server Class Guidelines

Choose host classes based on expected concurrency:

### Small Tier (Up to 100 concurrent participants)
- **CPU**: 2 vCPUs
- **RAM**: 4 GB
- **Storage**: 20 GB SSD

### Medium Tier (100 – 500 concurrent participants)
- **CPU**: 4 vCPUs
- **RAM**: 8 GB
- **Storage**: 50 GB SSD

### Large Tier (500 – 2000+ concurrent participants)
- **CPU**: 8 vCPUs+
- **RAM**: 16 GB+
- **Storage**: 100 GB+ NVMe SSD
