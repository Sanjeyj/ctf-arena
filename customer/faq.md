# Frequently Asked Questions (FAQ)
# CTF Arena v1.0.0 — EthicBids Technologies™

This document addresses standard participant and administrator questions regarding CTF Arena v1.0.0.

---

## 1. Participant Questions

### Q: Why did the points on my solved challenge decrease?
* **A**: The platform uses **dynamic scoring**. Challenge points automatically decay as more users submit correct solutions to balance the relative difficulty of challenges.

### Q: Are flag submissions case-sensitive?
* **A**: Yes. Flags must be submitted exactly as found, including casing and syntax wrappers (e.g. `flag{Casing_Is_Important}`).

---

## 2. Administrator Questions

### Q: How do I change the default rate limits?
* **A**: Edit the rate limits in `.env.production` (e.g., `RATE_LIMIT_LOGIN=5 per minute`) and restart the Gunicorn container.

### Q: How can I reset the scoreboard?
* **A**: Run the restore script (`scripts/restore.sh`) with the initial seed database to clear all solves.
