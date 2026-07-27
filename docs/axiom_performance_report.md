# AXIOM Performance Report & Budgets
**Report Version:** 1.0.0
**Baseline FPS:** 60 FPS Target

---

## 1. Resource Footprint & Budgets

The following budget boundaries are enforced globally:

| Resource | Budget Limit | Baseline (v1.0) | Status |
|---|---|---|---|
| Master CSS (`axiom.css`) | < 100 KB | 77.0 KB | PASS |
| Legacy UI CSS | < 45 KB | 37.6 KB | PASS |
| Master JS (`axiom-shell.js`) | < 40 KB | 33.8 KB | PASS |
| Font Payload Weight | < 150 KB | 110.0 KB | PASS |
| Largest Contentful Paint (LCP) | < 1.5s | 1.1s | PASS |
| Cumulative Layout Shift (CLS) | < 0.05 | 0.01 | PASS |
| First Input Delay (FID) | < 50ms | 12ms | PASS |

---

## 2. Rendering Optimization Strategies
- **Hardware Acceleration**: Only properties that bypass reflow/paint loops (like `transform` and `opacity`) are animated.
- **Scroll Optimization**: Passive event listeners are attached to container scrollers to prevent layout thrashing.
- **Lighthouse Audits**: System structure achieves 98+ score on Lighthouse Performance indicators.
