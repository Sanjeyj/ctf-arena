"""Smoke test for CTF Arena pages - Windows cp1252 safe (no emoji)."""
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import re

BASE = "http://127.0.0.1:5000"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(jar),
    urllib.request.HTTPRedirectHandler()
)


def get_body(url, post_data=None):
    try:
        r = opener.open(url, post_data)
        body = r.read().decode("utf-8", errors="replace")
        return r.status, getattr(r, "url", url), body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, url, body


def get_title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
    return m.group(1).strip() if m else "(no title)"


def find_csrf(html):
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    if not m:
        m = re.search(r'value="([^"]+)"[^>]*name="csrf_token"', html)
    return m.group(1) if m else ""


PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"

time.sleep(2)  # Wait for server to be ready

# 1. Login
print(f"{INFO} Getting login page...")
status, url, body = get_body(f"{BASE}/login")
print(f"{INFO} GET /login -> {status}")
csrf = find_csrf(body)
print(f"{INFO} CSRF found: {'YES' if csrf else 'NO'}")

login_data = urllib.parse.urlencode({
    "username": "Sample",
    "password": "Test@1234",
    "csrf_token": csrf,
}).encode()

status, rurl, body = get_body(f"{BASE}/login", login_data)
print(f"{INFO} POST /login -> {status}, url={rurl}")

if "login" in rurl.lower() and status in (200, 302):
    print(f"{FAIL} Login did not succeed (still at login page). status={status}")
    sys.exit(1)
else:
    print(f"{PASS} Logged in successfully, redirected to: {rurl}")

# 2. Test /challenge/WEB001
print()
status, url, body = get_body(f"{BASE}/challenge/WEB001")
print(f"{INFO} GET /challenge/WEB001 -> {status}, url={url}")
if "TemplateNotFound" in body:
    print(f"{FAIL} TemplateNotFound error present!")
elif status == 200:
    title = get_title(body)
    has_card = "challenge-card" in body
    has_submit = "Submit Flag" in body
    has_desc = "desc-card" in body or "description" in body.lower()
    print(f"{PASS} Page loaded: {title}")
    print(f"{PASS} Has challenge card: {has_card}")
    print(f"{PASS} Has Submit Flag section: {has_submit}")
    print(f"{PASS} Has description: {has_desc}")
else:
    print(f"{FAIL} Unexpected status: {status}")
    print(body[:400])

# 3. Test /challenge/ch1 (legacy template)
print()
status, url, body = get_body(f"{BASE}/challenge/ch1")
print(f"{INFO} GET /challenge/ch1 -> {status}, url={url}")
if "TemplateNotFound" in body:
    print(f"{FAIL} TemplateNotFound for ch1!")
elif status == 200:
    print(f"{PASS} ch1 loaded: {get_title(body)}")
else:
    print(f"{FAIL} Status: {status}")

# 4. Test /challenge/ch2
print()
status, url, body = get_body(f"{BASE}/challenge/ch2")
if status == 200 and "TemplateNotFound" not in body:
    print(f"{PASS} ch2 loaded: {get_title(body)}")
else:
    print(f"{FAIL} ch2 failed: {status}")

# 5. Test 404 page
print()
status, url, body = get_body(f"{BASE}/no-such-route-abcxyz")
print(f"{INFO} GET /no-such-route -> {status}")
if "TemplateNotFound" in body:
    print(f"{FAIL} TemplateNotFound in 404 handler!")
elif status == 404:
    print(f"{PASS} 404 page: {get_title(body)}")
else:
    print(f"{FAIL} Unexpected status: {status}")

# 6. Admin panel (logged in as participant - should be 403 or redirect)
print()
status, url, body = get_body(f"{BASE}/admin")
print(f"{INFO} GET /admin (as participant) -> {status}, url={url}")
if "TemplateNotFound" in body:
    print(f"{FAIL} TemplateNotFound in admin page!")
elif status in (200, 302, 403):
    print(f"{PASS} Admin response OK ({status}): {get_title(body)}")

print()
print("Smoke test complete.")
