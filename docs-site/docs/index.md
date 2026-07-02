# Welcome to CTF Arena

CTF Arena is a self-hosted, lightweight Capture The Flag (CTF) platform built using Flask, SQLAlchemy, and Tailwind CSS templates. It is designed to host college and community-level cybersecurity events with native Docker-based challenge environments.

---

## Key Features

- 🏠 **Challenge Grid**: Dynamic catalog filtering by category, search, or difficulty.
- 📡 **Live Scoreboard**: Real-time scoreboard streams powered by Server-Sent Events (SSE).
- ⏱️ **Dynamic Decay**: Points scale dynamically based on solve counts or competition time elapsed.
- 🔑 **Built-in RBAC**: Admin, Moderator, Challenge Author, and Participant privilege separation.
- 🐳 **Docker Exploits Sandbox**: Competitors provision their own isolated containers in a sandbox.
- 🧑‍🤝‍🧑 **Team Mode**: Form teams to combine scores on the leaderboard.
- 📊 **Metrics & Observability**: Native Prometheus `/metrics` and detailed `/health` endpoints.
