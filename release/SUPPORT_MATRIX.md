# System Support & Compatibility Matrix
# CTF Arena v1.0.0 — EthicBids Technologies™

This document defines the supported operating systems, runtime engines, databases, caches, browsers, and libraries for CTF Arena v1.0.0.

---

## 1. Operating Systems

| Environment | Supported OS | Target Version | Status |
|-------------|--------------|----------------|--------|
| **Production** | Ubuntu Server LTS | 20.04 LTS, 22.04 LTS, 24.04 LTS | Certified |
| **Production** | Debian GNU/Linux | 11 (Bullseye), 12 (Bookworm) | Certified |
| **Development** | macOS | 13 (Ventura), 14 (Sonoma) | Supported |
| **Development** | Microsoft Windows | Windows 10, Windows 11 | Supported |

---

## 2. Application Runtimes

| Component | Minimum Version | Recommended Version | Max Version |
|-----------|-----------------|---------------------|-------------|
| **Python** | 3.10 | 3.11 | 3.12 |
| **Node.js** *(Vercel deploy)* | 18.0.0 | 20.x | 22.x |

---

## 3. Databases & Cache Engines

| Service | Supported Engines | Certified Version | Rationale |
|---------|-------------------|-------------------|-----------|
| **Database Backend** | PostgreSQL | 14.x, 15.x, 16.x | Required for concurrency |
| **Database Backend** | SQLite | 3.35+ | For local development/testing only |
| **Cache & Rate-limiting** | Redis | 6.2+, 7.x | Required for session/rate limit sync |

---

## 4. Containerization & Orchestration

- **Docker Engine**: 24.0.0 or higher.
- **Docker Compose**: v2.20.0 or higher.
- **Kubernetes** *(Optional)*: v1.26 or higher.

---

## 5. Web Browsers

The modernized glassmorphic UI uses standard CSS grid/flexbox properties, verified across all major modern browser engines:

| Browser | Minimum Version | Status |
|---------|-----------------|--------|
| Google Chrome | 110+ | Fully Certified |
| Mozilla Firefox | 108+ | Fully Certified |
| Apple Safari | 15.6+ | Fully Certified |
| Microsoft Edge | 110+ | Fully Certified |

*Note: Internet Explorer and legacy non-Chromium Edge are not supported.*
