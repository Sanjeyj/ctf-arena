# UI Design System Reference — CTF Arena
**Version:** 1.0.0 (Batch A)
**File:** `static/css/ui-modernization.css`

---

## Design Philosophy

The CTF Arena UI design system implements a **Dark Futuristic Enterprise** aesthetic with **Restrained Glassmorphism** and a **Responsive 12-Column Bento Grid**. Every design decision prioritises:

- **Information density** — operators see critical data at a glance
- **Clarity** — strong hierarchy; no visual noise
- **Responsiveness** — full parity from 1920px down to 375px
- **Accessibility** — WCAG AA focus rings, reduced-motion support, semantic HTML

---

## CSS Variables (Design Tokens)

All tokens are defined on `:root` and available globally.

### Backgrounds

| Token | Value | Usage |
|---|---|---|
| `--ui-bg-primary` | `#060814` | Page background |
| `--ui-bg-secondary` | `#090d1a` | Section backgrounds |
| `--ui-bg-tertiary` | `#0c1122` | Nested zones |

### Glass Surfaces

| Token | Value | Usage |
|---|---|---|
| `--ui-surface` | `rgba(10,15,30,0.55)` | Standard glass card |
| `--ui-surface-strong` | `rgba(12,18,35,0.82)` | Modals, topbar |
| `--ui-surface-hover` | `rgba(16,24,48,0.70)` | Hover states |
| `--ui-surface-sidebar` | `rgba(8,12,24,0.90)` | Admin sidebar |

### Accent Colours

| Token | Hex | Usage |
|---|---|---|
| `--ui-cyan` | `#00f0ff` | Primary accent, CTF highlights |
| `--ui-violet` | `#8b5cf6` | Secondary accent, admin features |
| `--ui-success` | `#10b981` | Live/active states |
| `--ui-danger` | `#ef4444` | Alerts, destructive actions |
| `--ui-warning` | `#f59e0b` | Medium severity |

### Typography

| Token | Value |
|---|---|
| `--ui-font-interface` | `'Outfit', 'Segoe UI', system-ui, sans-serif` |
| `--ui-font-mono` | `'Fira Code', 'Cascadia Code', 'Consolas', monospace` |

### Layout

| Token | Value |
|---|---|
| `--ui-sidebar-width` | `256px` |
| `--ui-sidebar-width-collapsed` | `64px` |
| `--ui-header-height` | `56px` |

---

## Layout System

### Application Shell

All admin pages use the `.ui-shell` pattern:

```html
<body class="ui-app-bg">
  <!-- Sidebar overlay (mobile) -->
  <div id="sidebar-overlay" class="sidebar-overlay"></div>

  <!-- Navigation -->
  <nav id="admin-sidebar">...</nav>

  <!-- Top command bar -->
  <header class="ui-topbar">...</header>

  <!-- Content area -->
  <main class="ui-workspace" id="admin-workspace">
    {% block content %}...{% endblock %}
  </main>
</body>
```

### 12-Column Bento Grid

```html
<div class="ui-bento">
  <div class="ui-bento-3 ui-glass-card accent-cyan">Stat card</div>
  <div class="ui-bento-3 ui-glass-card accent-success">Stat card</div>
  <div class="ui-bento-6 ui-glass-card">Chart</div>
  <div class="ui-bento-12 ui-glass-card">Full-width table</div>
</div>
```

#### Column Span Classes

| Class | Columns | Default Width |
|---|---|---|
| `.ui-bento-2` | 2/12 | ~16.7% |
| `.ui-bento-3` | 3/12 | 25% |
| `.ui-bento-4` | 4/12 | 33.3% |
| `.ui-bento-6` | 6/12 | 50% |
| `.ui-bento-8` | 8/12 | 66.7% |
| `.ui-bento-9` | 9/12 | 75% |
| `.ui-bento-12` | 12/12 | 100% |

---

## Components

### Glass Cards

```html
<!-- Standard card -->
<div class="ui-glass-card">...</div>

<!-- Card with coloured accent edge -->
<div class="ui-glass-card accent-cyan">...</div>
<div class="ui-glass-card accent-violet">...</div>
<div class="ui-glass-card accent-success">...</div>
<div class="ui-glass-card accent-danger">...</div>
<div class="ui-glass-card accent-warning">...</div>

<!-- Stronger glass (for modals, auth) -->
<div class="ui-glass-strong">...</div>
```

### Metric Card

```html
<div class="ui-metric-card">
  <div class="ui-metric-label">Participants</div>
  <div class="ui-metric-value">24</div>
  <div class="ui-metric-sub">Registered users</div>
</div>
```

Value colour modifiers: `.violet`, `.success`, `.warning`, `.muted`

### Badges

```html
<span class="ui-badge ui-badge-cyan">Active</span>
<span class="ui-badge ui-badge-success">Passed</span>
<span class="ui-badge ui-badge-danger">Critical</span>
<span class="ui-badge ui-badge-warning">Medium</span>
<span class="ui-badge ui-badge-violet">Admin</span>
<span class="ui-badge ui-badge-muted">Inactive</span>
```

### Status Pill (topbar)

```html
<span class="ui-status-pill online">
  <span class="ui-pulse-dot"></span> Live
</span>
```

### Buttons

```html
<button class="ui-btn ui-btn-primary">Primary</button>
<button class="ui-btn ui-btn-ghost">Ghost</button>
<button class="ui-btn ui-btn-danger">Danger</button>
<button class="ui-btn ui-btn-violet">Violet</button>
<button class="ui-btn ui-btn-primary ui-btn-sm">Small</button>
```

### Forms

```html
<div class="ui-form-group">
  <label for="field-id" class="ui-label">Field Name</label>
  <input type="text" id="field-id" class="ui-input" placeholder="...">
</div>
```

### Auth Card (standalone login pages)

```html
<div class="ui-auth-card">
  <div class="ui-auth-logo">
    <span class="icon">🔑</span>
    <h1>Title <em>Accent</em><span class="ui-cursor">_</span></h1>
    <p>Subtitle</p>
  </div>
  <!-- error block if needed -->
  {% if error %}<div class="ui-error-msg">...</div>{% endif %}
  <form>...</form>
</div>
```

### Tables

```html
<div class="ui-table-wrap">
  <table class="ui-table">
    <thead><tr><th>Col</th></tr></thead>
    <tbody>
      <tr>
        <td class="mono cyan">value</td>
        <td class="muted">secondary</td>
      </tr>
    </tbody>
  </table>
</div>
```

### Progress Bars

```html
<div class="ui-bar-row">
  <div class="ui-bar-label">Challenge Name</div>
  <div class="ui-bar-track">
    <div class="ui-bar-fill" style="width:65%"></div>
  </div>
  <div class="ui-bar-count">13</div>
</div>
```

### Chart Container

```html
<div class="ui-chart-wrap">
  <canvas id="scoreChart"></canvas>
</div>
```

### Card Title

```html
<div class="ui-card-title">
  <span class="title-icon">📊</span> Section Title
</div>
```

---

## Batch D Design Extensions

The following design extensions were introduced in Batch D to support high-density metrics dashboards:

- **`.ui-badge-info`**: A blue-cyan badge background for informational or active items.
- **`.ui-section-heading`**: Uppercase section header element with border-bottom divider line.
- **`.ui-bento-card`**: Class ensuring bento grid cards support flexible min-heights and focus highlights.
- **`.ui-stat-row`**: Flex layout wrapping labels and values on single lines.
- **`.ui-empty-state`**: Layout wrapping empty results, styled with `.ui-empty-icon` and `.ui-empty-text`.

---

## Sidebar

The sidebar (`#admin-sidebar`) is controlled by `static/js/ui-shell.js`:

- **Desktop:** Collapses to icon-only mode (64px width). State persisted in `localStorage` under key `cdp_sidebar_collapsed`.
- **Mobile (≤768px):** Transforms into a sliding drawer. Toggle via `#sidebar-toggle`; close via overlay (`#sidebar-overlay`) or `Escape` key.
- **Active link:** Detected by matching `window.location.pathname`. Sets `aria-current="page"` and `.active` class.
- **Aria:** `aria-expanded` on `#sidebar-toggle` updates automatically.

---

## Responsive Breakpoints

| Breakpoint | Behaviour |
|---|---|
| ≤1280px | `bento-2` → span 3, `bento-3` → span 4, `bento-4` → span 6 |
| ≤1024px | Most bento items collapse to span 6 or 12 |
| ≤768px | Sidebar becomes drawer; workspace full-width; bento all → span 1 |
| ≤480px | Auth card padding reduced; page title smaller |

---

## Accessibility

- All interactive elements have `:focus-visible` cyan outline (2px, 2px offset)
- Sidebar links get `aria-current="page"` on active route
- Sidebar toggle has `aria-expanded` and `aria-controls` attributes
- `prefers-reduced-motion` disables all animations globally
- Custom scrollbar at 5px width with subtle track
