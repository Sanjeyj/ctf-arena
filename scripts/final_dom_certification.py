"""
Final DOM Certification — Cyber Defense Platform v1.0.0
Covers all admin routes across all batches (A–D) plus core participant routes.
"""
import io
import sys
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

from app import create_app

app = create_app()
app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
app.config["SERVER_NAME"] = None

# ---------------------------------------------------------------------------
# Route table: (path, must-contain title fragment, must-contain h1 fragment)
# ---------------------------------------------------------------------------
ADMIN_ROUTES = [
    # ── Core Shell ──────────────────────────────────────────────────────────
    ("/admin",                              "Admin Dashboard",              "Dashboard"),
    ("/admin/mission-control",              "Mission Control",              "Mission Control"),

    # ── SOC & Threat Operations (Batch B) ───────────────────────────────────
    ("/admin/soc",                          "SOC",                          "SOC"),
    ("/admin/threat-intel",                 "Threat Intelligence",          "Threat Intelligence"),
    ("/admin/cyberrange/incidents",         "Incident",                     "Incident"),
    ("/admin/hunts",                        "Threat Hunt",                  "Threat Hunt"),
    ("/admin/research/malware",             "Malware",                      "Malware"),
    ("/admin/research/campaigns",           "Campaign",                     "Campaign"),

    # ── GRC & Resilience (Batch C) ──────────────────────────────────────────
    ("/admin/resilience/vendors",           "Vendor Risk",                  "Vendor"),
    ("/admin/risk-quantification",          "Risk Quantification",          "Risk Quantification"),
    ("/admin/resilience",                   "Resilience",                   "Resilience"),
    ("/admin/compliance",                   "Compliance",                   "Compliance"),
    ("/admin/operations-fabric/chaos",      "Chaos",                        "Chaos"),
    ("/admin/systemic-resilience/contagion","Contagion",                    "Contagion"),

    # ── Assurance Fabric (Batch D) ──────────────────────────────────────────
    ("/admin/assurance",                    "Assurance",                    "Cyber Trust"),
    ("/admin/assurance/cases",              "Assurance Cases",              "Assurance Cases"),
    ("/admin/assurance/controls",           "Control Validation",           "Continuous Control"),
    ("/admin/assurance/devices",            "Device Posture",               "Device Compliance"),
    ("/admin/assurance/trust",              "Zero Trust",                   "Zero Trust"),
    ("/admin/assurance/supply-chain",       "Supply Chain",                 "Supply Chain"),

    # ── Validation Fabric (Batch D) ─────────────────────────────────────────
    ("/admin/validation-fabric",            "Validation Fabric",            "Continuous Security"),
    ("/admin/validation-fabric/campaigns",  "Validation Campaigns",         "Validation Campaigns"),
    ("/admin/validation-fabric/effectiveness","Defense Effectiveness",      "Defense Effectiveness"),
    ("/admin/validation-fabric/readiness",  "Readiness",                    "Playbook Readiness"),

    # ── Exposure Fabric (Batch D) ────────────────────────────────────────────
    ("/admin/exposure-fabric",              "Exposure Fabric",              "Security Architecture"),
    ("/admin/exposure-fabric/inventory",    "Inventory",                    "Exposed Assets"),
    ("/admin/exposure-fabric/findings",     "Findings",                     "Vulnerability"),
    ("/admin/exposure-fabric/paths",        "Attack Paths",                 "Attack Paths"),

    # ── Operations Fabric (Batch D) ──────────────────────────────────────────
    ("/admin/operations-fabric",            "Operations Fabric",            "Cyber Platform"),
    ("/admin/operations-fabric/health",     "Service Health",               "Platform Capabilities"),
    ("/admin/operations-fabric/incidents",  "Operational Incidents",        "Operational Incidents"),
    ("/admin/operations-fabric/telemetry",  "Telemetry",                    "Telemetry"),
    ("/admin/operations-fabric/traces",     "Distributed Tracing",          "Distributed Traces"),
]

PARTICIPANT_ROUTES = [
    ("/",         "CTF Arena",      "CTF"),
    ("/login",    "Login to the Arena", "Login"),
]

PASS = 0
FAIL = 0
ERRORS = []


def login_admin(client):
    return client.post(
        "/admin/login",
        data={"username": "admin", "password": "Admin@123"},
        follow_redirects=True,
    )


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        ERRORS.append(f"{label}: {detail}")
        print(f"  [FAIL] {label}  [{detail}]")


# ---------------------------------------------------------------------------
with app.test_client() as client:
    r = login_admin(client)
    check("Admin login", r.status_code == 200, f"status={r.status_code}")

    print("\n" + "=" * 66)
    print("  ADMIN ROUTES")
    print("=" * 66)
    for route, title_frag, h1_frag in ADMIN_ROUTES:
        print(f"\n-- {route}")
        try:
            resp = client.get(route, follow_redirects=True)
            html = resp.data.decode("utf-8", errors="replace")
            check("HTTP 200",         resp.status_code == 200,                       f"got {resp.status_code}")
            check(f"Title: {title_frag}",  title_frag.lower() in html.lower(),       "title mismatch")
            check(f"H1: {h1_frag}",        h1_frag.lower() in html.lower(),          "h1 mismatch")
            check("Sidebar present",       "ui-sidebar" in html or "sidebar" in html.lower(), "no sidebar")
            check("Glass card present",    "ui-glass-card" in html,                  "no glass card")
            check("No UndefinedError",     "UndefinedError" not in html,             "template var error")
            check("No 500",               resp.status_code != 500,                   "server error")
        except Exception as exc:
            FAIL += 1
            ERRORS.append(f"{route}: {exc}")
            print(f"  [FAIL] Exception: {exc}")

# Participant routes — use fresh unauthenticated client
with app.test_client() as anon:
    print("\n" + "=" * 66)
    print("  PARTICIPANT ROUTES (unauthenticated)")
    print("=" * 66)
    for route, title_frag, h1_frag in PARTICIPANT_ROUTES:
        print(f"\n-- {route}")
        try:
            resp = anon.get(route, follow_redirects=True)
            html = resp.data.decode("utf-8", errors="replace")
            check("HTTP 200", resp.status_code == 200, f"got {resp.status_code}")
            check(f"Title: {title_frag}", title_frag.lower() in html.lower(), "title mismatch")
        except Exception as exc:
            FAIL += 1
            ERRORS.append(f"{route}: {exc}")
            print(f"  [FAIL] Exception: {exc}")

# ---------------------------------------------------------------------------
total = PASS + FAIL
print("\n" + "=" * 66)
print("  FINAL DOM CERTIFICATION SUMMARY")
print("=" * 66)
print(f"  Routes tested : {len(ADMIN_ROUTES) + len(PARTICIPANT_ROUTES)}")
print(f"  Checks run    : {total}")
print(f"  PASSED        : {PASS}")
print(f"  FAILED        : {FAIL}")
print("=" * 66)

if ERRORS:
    print("\nFailed checks:")
    for e in ERRORS:
        print(f"  [FAIL] {e}")

if FAIL == 0:
    print("\n  FINAL DOM CERTIFICATION: ALL CHECKS PASSED")
    sys.exit(0)
else:
    print(f"\n  FINAL DOM CERTIFICATION: {FAIL} FAILED")
    sys.exit(1)
