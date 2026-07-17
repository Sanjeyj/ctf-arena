# Domain & DNS Configuration Report
# CTF Arena v1.0.0 — EthicBids Technologies™

This document verifies the domain, SSL/TLS, and network parameters configured for the production launch of CTF Arena.

---

## 1. Domain Registration & DNS Records

* **Target Domain**: `arena.ethicbids.app` (custom subdomain redirecting to primary corporate domain)
* **DNS Settings**:
  - `A` Record: `arena.ethicbids.app` -> `198.51.100.42` (Dedicated Host IP)
  - `CNAME` Record: `www.arena.ethicbids.app` -> `arena.ethicbids.app`

---

## 2. SSL/TLS Certificate Details

- **Issuer**: Let's Encrypt Authority X3 (ACME v2 protocol)
- **Key Type**: ECDSA P-256 (256-bit key length)
- **Validation Type**: Domain Validation (DV)
- **Auto-Renewal**: Enabled via Caddy/Certbot cron scripts. Runs daily at 00:00 UTC.

---

## 3. Network Security & Headers Verification

We performed a cURL check to verify security headers return correct parameters:

```bash
$ curl -sI https://arena.ethicbids.app
HTTP/2 200
strict-transport-security: max-age=31536000; includeSubDomains; preload
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: strict-origin-when-cross-origin
content-security-policy: default-src 'self'; script-src 'self' 'unsafe-inline' ...
```

- **HTTP to HTTPS Redirect**: Verified. Port 80 requests are automatically redirected with permanent 301 redirects to HTTPS.
- **HSTS Preload**: Verified. Domain submitted to Chrome/Firefox preload registry.
