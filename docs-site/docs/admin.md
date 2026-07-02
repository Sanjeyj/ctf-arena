# Administration & CLI Guide

Manage competition settings, reset scores, export standings, and perform maintenance using the Admin UI or the Flask CLI.

---

## 1. CLI Commands

Run commands from the virtual environment:

```bash
# Database Setup
flask db upgrade

# Seeding Initial Defaults
flask seed

# Reset all competitor scoreboards (DANGEROUS)
flask reset-scores

# Background task prune containers
flask prune-instances
```

---

## 2. Platform Monitoring

Check `/health` or scrape `/metrics` using Prometheus:

```yaml
# prometheus.yml config snippet
scrape_configs:
  - job_name: 'ctf-arena'
    static_configs:
      - targets: ['localhost:5000']
```
