# Monitoring Guide
# CTF Arena v1.0.0 — EthicBids Technologies™

## Overview

The CTF Arena monitoring stack uses **Prometheus** for metrics collection,
**Grafana** for visualization, and structured logs for operational observability.

---

## Architecture

```
CTF Arena App (/metrics) ──► Prometheus ──► Grafana Dashboards
Nginx (/stub_status)     ──►     │
PostgreSQL Exporter      ──►     │
Redis Exporter           ──►     │        ──► Alertmanager ──► PagerDuty / Slack
Node Exporter            ──►     │
```

---

## 1. Health Endpoint

The application exposes a health check endpoint at `/health`:

```bash
curl -s http://localhost:8000/health
# Expected: {"status": "ok"}
```

**Uptime monitors to configure:**
- UptimeRobot: check `/health` every 1 minute
- Prometheus `probe_success` metric via `blackbox_exporter`

---

## 2. Metrics Endpoint

The application exposes Prometheus metrics at `/metrics` when `METRICS_ENABLED=True`:

```bash
curl -s http://localhost:8000/metrics | head -20
```

### Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `flask_http_request_duration_seconds` | Request latency histogram | p99 > 2s |
| `flask_http_request_total` | Request count by status | 5xx rate > 1% |
| `flask_http_requests_in_progress` | Active concurrent requests | > 100 |
| `process_resident_memory_bytes` | App memory usage | > 900 MB |
| `process_open_fds` | Open file descriptors | > 500 |

---

## 3. Database Monitoring (PostgreSQL)

Deploy `postgres-exporter` alongside the database container.

### Key PostgreSQL Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `pg_up` | Database reachability | == 0 for > 30s |
| `pg_database_size_bytes` | Database size | > 10 GB |
| `pg_stat_activity_count` | Active connections | > 80 |
| `pg_stat_database_deadlocks` | Deadlock count | > 0 |
| `pg_stat_database_blks_hit_ratio` | Cache hit ratio | < 0.95 |

---

## 4. Redis Monitoring

Deploy `redis-exporter` alongside the Redis container.

### Key Redis Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `redis_up` | Redis reachability | == 0 for > 30s |
| `redis_memory_used_bytes` | Memory usage | > 100 MB |
| `redis_connected_clients` | Client connections | > 50 |
| `redis_keyspace_hits_total` | Cache hits | — |
| `redis_keyspace_misses_total` | Cache misses | miss rate > 30% |

---

## 5. System / Host Monitoring (Node Exporter)

Deploy `node-exporter` on the host.

### Key Host Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `node_cpu_seconds_total` | CPU usage | > 90% for 5 min |
| `node_memory_MemAvailable_bytes` | Free memory | < 200 MB |
| `node_filesystem_avail_bytes` | Disk space | < 10% free |
| `node_disk_io_time_seconds_total` | Disk I/O wait | — |
| `node_network_receive_errs_total` | Network errors | > 10/min |

---

## 6. Log Management

### Log Sources

| Source | Location | Format |
|--------|----------|--------|
| Gunicorn access log | `logs/access.log` | Combined NCSA |
| Gunicorn error log | `logs/error.log` | Text |
| Nginx access log | Docker log stream | JSON |
| Application log | `logs/app.log` | JSON |

### Log Collection (Recommended)
Use **Loki** + **Promtail** for log aggregation into Grafana:

```yaml
# promtail config snippet
scrape_configs:
  - job_name: ctf-arena-logs
    static_configs:
      - targets: ['localhost']
        labels:
          job: ctf-arena
          __path__: /app/logs/*.log
```

---

## 7. Alert Recommendations

### Critical Alerts (PagerDuty / immediate)

| Alert | Condition | Action |
|-------|-----------|--------|
| Application Down | `/health` returns non-200 for > 60s | Restart app container |
| Database Down | `pg_up == 0` for > 30s | Check DB container, restore from backup |
| Redis Down | `redis_up == 0` for > 30s | Restart Redis, check rate-limit storage |
| Disk Full | `node_filesystem_avail_bytes < 5%` | Clean logs, expand storage |
| High Error Rate | HTTP 5xx > 5% for 5 min | Check app logs, rollback if needed |

### Warning Alerts (Slack / business hours)

| Alert | Condition |
|-------|-----------|
| High Memory | App process > 800 MB |
| High CPU | Host CPU > 80% for 10 min |
| Slow Responses | p99 latency > 1s for 5 min |
| Low Cache Hit | Redis miss rate > 20% |
| Database Size | DB > 5 GB |

---

## 8. Grafana Dashboard Access

- **URL**: `http://your-domain.com:3000` (or via reverse proxy at `/grafana`)
- **Default credentials**: Set via `GRAFANA_ADMIN_USER` / `GRAFANA_PASSWORD` env vars
- **Pre-built dashboards**: Import from Grafana.com
  - Node Exporter Full: `1860`
  - PostgreSQL Database: `9628`
  - Redis: `763`

---

## 9. Monitoring Deployment Checklist

| Task | Status |
|------|--------|
| Prometheus running and scraping app | ☐ |
| Grafana connected to Prometheus | ☐ |
| `/health` returning 200 | ☐ |
| `/metrics` returning data | ☐ |
| Node Exporter deployed | ☐ |
| Postgres Exporter deployed | ☐ |
| Redis Exporter deployed | ☐ |
| Alerting rules configured | ☐ |
| Log collection configured | ☐ |
| Dashboard access verified | ☐ |
| On-call rotation defined | ☐ |
