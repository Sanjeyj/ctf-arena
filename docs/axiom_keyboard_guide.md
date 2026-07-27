# AXIOM Keyboard Navigation & Shortcuts Guide
**Release Version:** 1.0.0

AXIOM implements a keyboard-first navigation model to accelerate security analyst workflows.

---

## 1. Global Keyboard Shortcuts

| Shortcut | Action | Scope |
|---|---|---|
| `Ctrl + K` or `Cmd + K` | Toggle Command Palette | Global |
| `Ctrl + /` | Toggle / Collapse Sidebar Pinned State | Global |
| `Escape` | Dismiss Modals, Dropdowns, and Drawers | Active Overlay |
| `Tab` | Move to next focusable element | Document |
| `Shift + Tab` | Move to previous focusable element | Document |
| `Up / Down Arrows` | Scroll Command Palette list elements | active dropdown / search list |
| `Enter` | Select active list element | active focus element |

---

## 2. Input Field Focus Rules
- Keypress event listeners check `document.activeElement` to prevent capturing keys when user is typing inside text inputs, textareas, or select dropdowns.
- Opening a modal/command palette overlays focuses on the primary text input instantly.
- When overlays are closed, focus returns to the triggering element.
