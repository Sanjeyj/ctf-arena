# Monitoring & Observability Activation
# CTF Arena v1.0.0 — EthicBids Technologies™

This document confirms that the monitoring, alerting, and logging infrastructure is active and operational for the production launch.

---

## 1. Activated Monitoring Streams

The following observability hooks are fully configured and verified:

### A. Health Monitoring
- Daily uptime ping checks target the `/health` endpoint.
- Alerting rules configure instant SMS/email dispatch if the target endpoint remains unreachable for > 60 seconds.

### B. Metrics Scrapes (Prometheus)
- Prometheus is running and scraping the application's `/metrics` route on a 15-second loop.
- **Scraped targets verified**:
  * Flask App Metrics (HTTP latencies, error counts, CPU usage)
  * PostgreSQL Database connection pool usage
  * Redis rate-limiting hit rates
  * Host operating system hardware constraints (Node Exporter)

### C. Log Aggregation
- System access and error log streams write to persistent `/app/logs/` directories.
- Log rotation script (`ctf-arena-janitor`) runs on a weekly timer to archive and compress older logs.

### D. Alert Thresholds
- **Disk Space**: Alerts trigger if disk storage exceeds 80%.
- **High CPU**: Alerts trigger if CPU utilization exceeds 75% for > 15 minutes.
- **Application Error Rate**: Alerts trigger if HTTP 5xx responses exceed 1% of total traffic.
