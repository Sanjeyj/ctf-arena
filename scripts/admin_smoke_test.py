"""Admin smoke test - tests admin panel pages."""
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import re
import time

BASE = "http://127.0.0.1:5000"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(jar),
    urllib.request.HTTPRedirectHandler()
)

def get_body(url, data=None):
    try:
        r = opener.open(url, data)
        body = r.read().decode("utf-8", errors="replace")
        return r.status, getattr(r, "url", url), body
    except urllib.error.HTTPError as e:
        return e.code, url, e.read().decode("utf-8", errors="replace")

def find_csrf(html):
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else ""

def get_title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
    return m.group(1).strip() if m else "?"

time.sleep(1)

# Admin login
_, _, body = get_body(f"{BASE}/admin/login")
csrf = find_csrf(body)
data = urllib.parse.urlencode({
    "username": "admin",
    "password": "Admin@123",
    "csrf_token": csrf
}).encode()
s, url, body = get_body(f"{BASE}/admin/login", data)
print(f"Admin login -> {s}, url={url}")

# Test admin pages
pages = [
    "/admin",
    "/admin/challenges",
    "/admin/submissions",
]

for path in pages:
    s, url, body = get_body(f"{BASE}{path}")
    ok = "TemplateNotFound" not in body and s == 200
    label = "[PASS]" if ok else "[FAIL]"
    t = get_title(body)[:60]
    print(f"{label} {path} -> {s}: {t}")
    if not ok:
        print("  Body snippet:", body[:200])

print()
print("Admin smoke test complete.")
