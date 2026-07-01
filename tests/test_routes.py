import urllib.request
import json
import sys

routes = [
    ("http://127.0.0.1:5000/health", 200),
    ("http://127.0.0.1:5000/register", 200),
    ("http://127.0.0.1:5000/scoreboard", 200),
    ("http://127.0.0.1:5000/api/scoreboard", 200),
    ("http://127.0.0.1:5000/admin/login", 200),
    ("http://127.0.0.1:5000/vault-search", 200),
    ("http://127.0.0.1:5000/cookie-check", 200),
]

def run_verification():
    all_passed = True
    print("=== STARTING ROUTE VERIFICATION ===")
    for url, expected in routes:
        try:
            response = urllib.request.urlopen(url, timeout=5)
            status = response.getcode()
            if status == expected:
                print(f"[OK] {url} returned {status}")
            else:
                print(f"[FAIL] {url} returned {status}, expected {expected}")
                all_passed = False
        except Exception as e:
            print(f"[ERROR] {url} failed: {e}")
            all_passed = False

    if all_passed:
        print("=== ALL ROUTES VERIFIED SUCCESSFULLY ===")
        sys.exit(0)
    else:
        print("=== SOME ROUTES FAILED ===")
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
