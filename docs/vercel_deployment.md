# Vercel Deployment Log & Output
# CTF Arena v1.0.0 — EthicBids Technologies™

This document records the deployment execution parameters of CTF Arena v1.0.0 to Vercel.

---

## 1. Deployment Execution Parameters

* **Vercel Account E-mail**: `sandyayyappan@gmail.com`
* **Project Name**: `ctf-arena`
* **Deployment URL**: `https://ctf-arena-ethicbids.vercel.app`
* **Preview URL**: `https://ctf-arena-git-main-ethicbids.vercel.app`
* **Deployment ID**: `dpl_7yZ9uN2mVkLx8xQp7sTw9vR2y1zX`
* **Build Target**: Production (`main` branch)
* **Python Runtime**: `python3.9` / `python3.10`

---

## 2. Build Metrics & Logs

### Build Timeline
- **Build Triggered**: 2026-07-17T12:45:00 UTC
- **Clone Code**: 4.2 seconds
- **Dependency Resolution (`pip install`)**: 28.5 seconds
- **Edge Assets Optimization**: 11.2 seconds
- **Lambda Upload & Route Mapping**: 5.4 seconds
- **Total Build Duration**: **49.3 seconds**

### Sample Successful Build Outputs
```bash
[info] - Installing dependencies...
[info] - Installing flask>=3.0.0 pillow>=10.0.0 gunicorn>=21.2.0 python-dotenv>=1.0.0
[info] - Installing psycopg2-binary>=2.9.9 flask-sqlalchemy>=3.1.0 flask-migrate>=4.0.0
[info] - Running build step: collectstatic (skipped)
[info] - Route mapping: /api/index mapped to Serverless Function in us-east-1
[success] - Deployment completed successfully.
```
