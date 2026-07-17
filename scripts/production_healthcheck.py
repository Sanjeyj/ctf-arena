#!/usr/bin/env python3
"""
CTF Arena v1.0.0 — Production Health Check Script
EthicBids Technologies™

Validates that the application is healthy and all certified production routes respond correctly.
Exits 0 on success, 1 on any failure.

Usage:
    python scripts/production_healthcheck.py
    python scripts/production_healthcheck.py --base-url http://your-domain.com
"""
import sys
import time
import argparse
import urllib.request
import urllib.error
import urllib.parse

# ── Configuration ─────────────────────────────────────────────────────────────
PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"
INFO = "[INFO]"

results = {"passed": 0, "failed": 0, "warned": 0}


def check(label: str, url: str, expected_statuses: list = [200],
          contains: str = None, not_contains: str = None,
          timeout: int = 10) -> bool:
    """Perform a single health check."""
    try:
        req = urllib.request.Request(url, method="GET")
        
        # We use a custom redirect handler to capture 302 redirect status code if it occurs
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                # Raise an exception with the code so we can capture it instead of auto-following
                raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)

        opener = urllib.request.build_opener(NoRedirectHandler(), urllib.request.HTTPCookieProcessor())
        
        try:
            with opener.open(req, timeout=timeout) as resp:
                status = resp.status
                body = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            status = e.code
            body = e.read().decode("utf-8", errors="replace") if hasattr(e, 'read') else ""
            
        ok = (status in expected_statuses)
        if ok and contains and contains not in body:
            ok = False
        if ok and not_contains and not_contains in body:
            ok = False

        if ok:
            print(f"  {PASS} {label} — HTTP {status}")
            results["passed"] += 1
            return True
        else:
            print(f"  {FAIL} {label} — HTTP {status} (expected one of {expected_statuses})")
            results["failed"] += 1
            return False

    except Exception as e:
        print(f"  {FAIL} {label} — {type(e).__name__}: {e}")
        results["failed"] += 1
        return False


def main():
    parser = argparse.ArgumentParser(description="CTF Arena Production Health Check")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000",
                        help="Base URL of the application")
    parser.add_argument("--timeout", type=int, default=10)
    args = parser.parse_args()

    BASE = args.base_url.rstrip("/")
    T = args.timeout

    print(f"\n{'='*60}")
    print(f"  CTF Arena v1.0.0 — Production Health Check")
    print(f"  EthicBids Technologies™")
    print(f"  Target: {BASE}")
    print(f"  Time:   {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print(f"{'='*60}\n")

    # ── Health Endpoint ────────────────────────────────────────────────────
    print("[ Health Endpoint ]")
    check("GET /health", f"{BASE}/health", [200])
    print()

    # ── Unauthenticated Public Routes ──────────────────────────────────────
    print("[ Public Routes ]")
    check("GET /login", f"{BASE}/login", [200])
    check("GET /register", f"{BASE}/register", [200])
    check("GET /admin/login", f"{BASE}/admin/login", [200])
    print()

    # ── Authenticated Required (should redirect to login or return 200) ────
    print("[ Auth-Required Routes — expect redirect or login ]")
    check("GET /", f"{BASE}/", [200, 302])
    check("GET /scoreboard", f"{BASE}/scoreboard", [200, 302])
    print()

    # ── Admin Enclaves (should redirect to admin login or return 200/302) ──
    print("[ Admin Enclave Routes ]")
    check("GET /admin", f"{BASE}/admin", [200, 302])
    check("GET /admin/mission-control", f"{BASE}/admin/mission-control", [200, 302])
    check("GET /admin/soc", f"{BASE}/admin/soc", [200, 302])
    check("GET /admin/threat-intel", f"{BASE}/admin/threat-intel", [200, 302])
    check("GET /admin/resilience/vendors", f"{BASE}/admin/resilience/vendors", [200, 302])
    check("GET /admin/risk-quantification", f"{BASE}/admin/risk-quantification", [200, 302])
    check("GET /admin/compliance", f"{BASE}/admin/compliance", [200, 302])
    print()

    # ── Platform Fabric Routes ─────────────────────────────────────────────
    print("[ Platform Fabric Enclaves ]")
    check("GET /admin/assurance", f"{BASE}/admin/assurance", [200, 302])
    check("GET /admin/validation-fabric", f"{BASE}/admin/validation-fabric", [200, 302])
    check("GET /admin/exposure-fabric", f"{BASE}/admin/exposure-fabric", [200, 302])
    check("GET /admin/operations-fabric", f"{BASE}/admin/operations-fabric", [200, 302])
    print()

    # ── Static Assets ──────────────────────────────────────────────────────
    print("[ Static Assets ]")
    check("GET /static/css/ui-modernization.css", f"{BASE}/static/css/ui-modernization.css", [200])
    check("GET /static/js/ui-shell.js", f"{BASE}/static/js/ui-shell.js", [200])
    print()

    # ── Error Pages ────────────────────────────────────────────────────────
    print("[ Error Pages ]")
    check("GET /nonexistent-route-xyz", f"{BASE}/nonexistent-route-xyz", [404])
    print()

    # ── Summary ───────────────────────────────────────────────────────────
    total = results["passed"] + results["failed"] + results["warned"]
    print(f"{'='*60}")
    print(f"  PRODUCTION HEALTH CHECK SUMMARY")
    print(f"  Checks run : {total}")
    print(f"  PASSED     : {results['passed']}")
    print(f"  FAILED     : {results['failed']}")
    print(f"  WARNED     : {results['warned']}")
    print()

    if results["failed"] == 0:
        print(f"  [SUCCESS] PRODUCTION HEALTH CHECK PASSED")
    else:
        print(f"  [FAILURE] PRODUCTION HEALTH CHECK FAILED — {results['failed']} failure(s)")

    print(f"{'='*60}\n")
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
