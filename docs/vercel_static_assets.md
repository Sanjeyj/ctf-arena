# Vercel Static Assets Serving
# CTF Arena v1.0.0 — EthicBids Technologies™

This document outlines the strategy for serving static assets (CSS, JS, Fonts, Images) when running on Vercel.

---

## 1. Static Asset Serving Architecture

Vercel serves static assets directly from its Edge CDN without routing requests to the Python serverless function, which reduces latency and saves serverless execution time.

- **Directory Mapping**: Vercel automatically matches `/static/` requests to the repository's `static/` directory.
- **Cache-Control Headers**: Assets served via Vercel are automatically configured with long-term caching headers:
  `Cache-Control: public, max-age=31536000, immutable`

---

## 2. Layout Integrity Verifications

All core static files are packaged in the repository:
- **Stylesheets**: `static/css/ui-modernization.css`
- **JavaScript**: `static/js/ui-shell.js`
- **Asset paths**: Resolved using `url_for('static', filename='...')` inside HTML templates.

This ensures asset links render properly on Vercel edge networks.
