# Mobile Platform — Research Initiative
# CTF Arena v2.0 — EthicBids Technologies™
# Research Phase | Not for Production

---

## 1. Vision

Extend the CTF Arena to native mobile (Android & iOS) and Progressive Web App (PWA) experiences, enabling participants to engage in challenges, receive push notifications, and view scoreboards from any device — even offline.

---

## 2. Platform Strategy

| Platform | Technology | Priority |
|---|---|---|
| **PWA** | Service Workers + Web App Manifest (works today on desktop + mobile) | **P1 — Earliest delivery** |
| **Android** | Kotlin + Jetpack Compose | P2 |
| **iOS** | Swift + SwiftUI | P2 |
| **Cross-Platform** | React Native or Flutter (if native is deferred) | P3 (fallback) |

---

## 3. PWA — Immediate Path

The existing Flask app can be extended to a PWA by adding:
```html
<!-- _pwa_manifest.json -->
{
  "name": "CTF Arena",
  "short_name": "CTFArena",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0d0f1a",
  "theme_color": "#00f0ff",
  "icons": [
    { "src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```
- **Service Worker**: Caches scoreboard, challenge list, and static assets for offline viewing.
- **Push Notifications**: Web Push API for challenge unlocks and incident alerts.

---

## 4. Native App Feature Set

| Feature | PWA | Android/iOS |
|---|---|---|
| Challenge browser | ✅ | ✅ |
| Flag submission | ✅ | ✅ |
| Live scoreboard | ✅ (SSE) | ✅ (WebSocket) |
| Push notifications | ✅ (Web Push) | ✅ (FCM / APNs) |
| Offline mode | ✅ (Service Worker cache) | ✅ (local SQLite cache) |
| Biometric auth | ❌ | ✅ (FaceID / Fingerprint) |
| Kubernetes lab access | ❌ | ✅ (SSH terminal in-app) |

---

## 5. Implementation Roadmap

| Phase | Duration | Deliverable |
|---|---|---|
| **Alpha** | Q1 2027 | PWA manifest + Service Worker + push notifications |
| **Beta** | Q2 2027 | Android native app (Kotlin) |
| **GA** | Q3 2027 | iOS native app (Swift), biometric auth |

---

## 6. Status

**RESEARCH PHASE** — The current web app is mobile-responsive via CSS. Native apps not yet started.
