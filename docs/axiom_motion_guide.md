# AXIOM Motion & Animation Guide
**Release Version:** 1.0.0

Animations in AXIOM are functional: they guide attention, provide feedback, and explain structural transitions.

---

## 1. Timing Parameters
- **Micro (`100ms`)**: Focus ring transitions, simple hover highlights, status changes.
- **Fast (`150ms`)**: Button clicks, badge updates, input active indicators.
- **Context (`180ms`)**: Context panel hover slide-out, rail icon hover highlight.
- **Base (`200ms`)**: Timeline milestone transitions, panel shifts.
- **Slow (`350ms`)**: Command Palette overlay scale-in, dialog boxes.

---

## 2. Easing Scale
- **`ease-out`**: `cubic-bezier(0, 0, 0.2, 1)` (Elements entering screen).
- **`ease-in`**: `cubic-bezier(0.4, 0, 1, 1)` (Elements exiting screen).
- **`ease-inout`**: `cubic-bezier(0.4, 0, 0.2, 1)` (Elements morphing state).
- **`ease-spring`**: `cubic-bezier(0.34, 1.56, 0.64, 1)` (Small triggers/tooltips).

---

## 3. GPU Acceleration & Motion Preferences
- Animations must animate ONLY `transform` and `opacity` properties.
- Under `@media (prefers-reduced-motion: reduce)`, all transitions are set to `0s` to guarantee instant visual response.
