# Performance Regression Testing
# CTF Arena v1.0.0 — EthicBids Technologies™

This document defines performance benchmarks and response latency checks to prevent degradation during minor updates.

---

## 1. Performance Benchmarks

All patches must adhere to the following limits:

* **Startup Overhead**: Flask app factory setup must complete in **< 1.5 seconds**.
* **Page Load Latency**: Core HTML pages must render and return headers in **< 200ms** under normal load.
* **API Response Time**: Flag validation API `/submit` must respond within **< 500ms**.
* **Memory Footprint**: App container base idle memory must not exceed **250 MB**.

---

## 2. Load Testing Guidelines

Prior to major events, run a load simulation using **Locust**:

```python
# Locust load testing script structure
from locust import HttpUser, task, between

class CTFPlayer(HttpUser):
    wait_time = between(1, 5)

    @task
    def load_home(self):
        self.client.get("/")

    @task
    def load_scoreboard(self):
        self.client.get("/scoreboard")
```

**Target Load Target**: Maintain p95 response time < 1.0s under 1000 concurrent virtual users.
