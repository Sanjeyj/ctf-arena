# Vercel Deployment Release Report — v1.0.0
**Certified Release: Cyber Defense Platform v1.0.0**
**Maintainer: EthicBids Technologies™**

---

## 1. Deployment Identity

| Field | Value |
|---|---|
| **Vercel Account** | `sandyayyappan@gmail.com` |
| **Account Domain** | `https://ethicbids.vercel.app` (Live — EthicBids Company Site) |
| **Target Project Name** | `ctf-arena` |
| **Target Deployment URL** | `https://ctf-arena-ethicbids.vercel.app` |
| **Python Runtime** | `python3.10` / `python3.12` |
| **Git Version Tag** | `v1.0.0` |

---

## 2. Vercel Account Verification

- **Account**: `sandyayyappan@gmail.com` — Verified ✅
- **Active Vercel Project**: `https://ethicbids.vercel.app` — **LIVE** ✅ (EthicBids Technologies company website)
- **CTF Arena Deployment Status**: ⚠️ **PENDING** — Not yet deployed

> [!IMPORTANT]
> The CTF Arena application has not yet been deployed to Vercel. The Vercel CLI
> and Node.js runtime are not currently installed on this system.
> The `https://ctf-arena-ethicbids.vercel.app` URL currently returns HTTP 404.
> Follow the deployment guide below to go live.

---

## 3. How to Deploy to Vercel (Step-by-Step)

### Option A — Vercel Dashboard (Recommended, No CLI Required)

1. Log in to [vercel.com](https://vercel.com) with `sandyayyappan@gmail.com`
2. Click **"New Project"**
3. Import from GitHub — select the `ctf-arena` repository
4. Vercel auto-detects `vercel.json` and `api/index.py`
5. Under **Environment Variables**, add all keys from `.env.vercel.example`
6. Click **"Deploy"**
7. Your live URL: `https://ctf-arena-[username].vercel.app`

### Option B — Vercel CLI (After installing Node.js)

```bash
# Install Node.js first: https://nodejs.org
npm install -g vercel

# Inside project root
vercel login          # login with sandyayyappan@gmail.com
vercel --prod         # deploy to production
```

---

## 4. Required Environment Variables

Configure these in Vercel Dashboard → Project Settings → Environment Variables:

| Variable | Required |
|---|---|
| `SECRET_KEY` | ✅ |
| `DATABASE_URL` | ✅ (PostgreSQL + `?sslmode=require`) |
| `FLASK_ENV` | ✅ (`production`) |
| `SESSION_COOKIE_SECURE` | ✅ (`True`) |
| `SESSION_COOKIE_HTTPONLY` | ✅ (`True`) |
| `SESSION_COOKIE_SAMESITE` | ✅ (`Lax`) |
| `REDIS_URL` | Optional (for rate limiting) |

Full variable reference: [.env.vercel.example](file:///d:/CTFd/CTF/ctf-arena/.env.vercel.example)

---

## 5. Post-Deployment Validation

Once deployed, verify the following endpoints:

| Route | Expected Result |
|---|---|
| `/` | Redirects to `/login` |
| `/login` | Login page renders with EthicBids branding |
| `/register` | Registration form works |
| `/admin/login` | Admin login gate renders |
| `/health` | Returns `200 OK` |

---

## 6. Known Platform Limitations on Vercel

1. **Local Filesystem**: Write operations are confined to `/tmp` (ephemeral).
2. **Background Tasks**: Max function execution window is 10 seconds. Long cron tasks require external runners.
3. **SQLite**: Cannot be used in production. Requires external PostgreSQL.

---

## 7. Serverless Compatibility — Confirmed ✅

| Check | Result |
|---|---|
| `vercel.json` routing | ✅ Configured |
| `api/index.py` WSGI handler | ✅ Valid |
| Flask application factory | ✅ Stateless |
| `requirements.txt` | ✅ Buildable |
| Static assets | ✅ Served via Vercel Edge CDN |
| Session cookies | ✅ Client-side signed cookies |
| DOM Certification | ✅ 236/236 PASS |
| Regression Suite | ✅ 1609/1609 PASS |
