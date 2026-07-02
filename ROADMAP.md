# Product Roadmap — CTF Arena

This document outlines the planned future direction and key milestones for the CTF Arena project.

---

## Current Release: v1.0.0 (Release Candidate)
- Production-ready core package factory pattern.
- Fully validated PostgreSQL and SQLite support.
- Native dynamic scoring engine and teams management.
- Ephemeral Docker container challenge deployments.
- Full security audits and Prometheus observability metrics.

---

## Near-Term Roadmap

### Milestone v1.1 — Plugin Marketplace Architecture (Phase 13)
- Design and document standard hook injection points.
- Expose a structured Plugin API so community modules can extend pages, themes, and logic.
- Create a directory for community contribution sharing.

### Milestone v1.2 — Themes and Theme Marketplace (Phase 13.5)
- Standardize HTML layout theme overrides.
- Enable organizers to swap between dark, retro, cyberpunk, and minimal interfaces with a single config toggle.

---

## Mid-Term Roadmap

### Milestone v2.0 — AI Challenge Assistant (Phase 14)
- Integrate an LLM-based challenge generator.
- Help admins write descriptions, generate flags, construct Docker exploit sandbox templates, and write hints dynamically from the admin panel.

---

## Long-Term Vision

### Milestone v3.0 — Multi-Tenant SaaS Edition (Phase 15)
- Support hosting multiple concurrent CTF competitions from a single deployment instance.
- Provide sub-domain isolation, per-competition config namespaces, and custom scoreboards.

### Milestone v4.0 — Global CTF Hosting Platform (Phase 16)
- Scale challenges across elastic Kubernetes clusters.
- Auto-scale user environments to support 10,000+ concurrent global exploit competitors.
