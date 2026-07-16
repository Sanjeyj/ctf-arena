# UI Component Catalog — Cyber Defense Platform (CTF Arena)

This catalog documents the reusable styles, layout patterns, and interface components implemented in the UI Modernization Directive (Batch A and Batch B). All components are defined in `static/css/ui-modernization.css` and use native HTML and Vanilla CSS variables.

---

## 1. Application Shell & Workspace

The layout shell provides the primary responsive container structure.

### Workspace Container
```html
<main class="ui-workspace" id="admin-workspace">
  {% block content %}{% endblock %}
</main>
```

### Page Header
Used at the top of sub-dashboards to present titles, descriptions, and action/status pills.
```html
<div class="ui-page-header" style="display: flex; justify-content: space-between; align-items: center;">
    <div>
        <div class="ui-page-title">🛡️ SOC Operations <em>Center</em></div>
        <div class="ui-page-subtitle">Security Operations & Threat Intelligence command dashboard.</div>
    </div>
    <div class="ui-status-pill online">
        <span class="ui-pulse-dot"></span> LIVE MONITORING
    </div>
</div>
```

---

## 2. Grid & Layout

### Responsive Bento Grid
A 12-column grid that automatically adjusts grid tracks based on media query breakpoints.
```html
<div class="ui-bento">
  <div class="ui-bento-4 ui-glass-card">Card (1/3rd width)</div>
  <div class="ui-bento-8 ui-glass-card">Card (2/3rds width)</div>
  <div class="ui-bento-12 ui-glass-card">Full-width Card</div>
</div>
```

#### Bento Sizing Classes:
- `.ui-bento-2`: Spans 2 out of 12 columns (~16.6% width).
- `.ui-bento-3`: Spans 3 out of 12 columns (25% width).
- `.ui-bento-4`: Spans 4 out of 12 columns (33.3% width).
- `.ui-bento-6`: Spans 6 out of 12 columns (50% width).
- `.ui-bento-8`: Spans 8 out of 12 columns (66.6% width).
- `.ui-bento-9`: Spans 9 out of 12 columns (75% width).
- `.ui-bento-12`: Spans 12 out of 12 columns (100% width).

---

## 3. Cards & Containers

### Standard Glass Card (`.ui-glass-card`)
A frosted glass surface with subtle borders and shadows.
```html
<div class="ui-glass-card">
    <div class="ui-card-title">
        <span class="title-icon">📊</span> Card Title
    </div>
    <p>Card content goes here.</p>
</div>
```

### Card Accents
Add an accent color border to the top of any `.ui-glass-card`.
- `.accent-cyan`: Cyan highlight.
- `.accent-violet`: Violet highlight.
- `.accent-success`: Success Green highlight.
- `.accent-danger`: Red alert highlight.
- `.accent-warning`: Amber warning highlight.

```html
<div class="ui-glass-card accent-cyan">
    <!-- Content -->
</div>
```

### Interactive Glass Link Card (`.ui-glass`)
Used for clickable tiles or lists that change color on hover.
```html
<a href="#" class="ui-glass" style="display: block; padding: 1rem; border-radius: var(--ui-radius-md); text-decoration: none;">
    <h4>Link Title</h4>
    <p class="muted">Description text.</p>
</a>
```

---

## 4. Typography & Utility Classes

### Headings
- `.ui-page-title`: Large bold title (`1.55rem`) with cyan accents using `<em>`.
- `.ui-page-subtitle`: Subtext description font size (`0.9rem`).
- `.ui-card-title`: Section titles for within cards (`1rem`).

### Monospace / Colors
- `.mono`: Swaps typeface to Fira Code/monospace.
- Color helpers (e.g., `.cyan`, `.violet`, `.success`, `.warning`, `.muted`):
```html
<span class="mono cyan">IP Address</span>
<span class="muted">Secondary text</span>
```

---

## 5. Forms & Inputs

### Text Inputs
```html
<div class="ui-form-group">
    <label for="input-demo" class="ui-label">Username</label>
    <input type="text" id="input-demo" class="ui-input" placeholder="Type here...">
</div>
```

### Select Controls (`.ui-select`)
Custom-styled drop-down selector with custom SVG arrows.
```html
<select class="ui-select">
    <option value="all">All Items</option>
    <option value="filter">Filter Option</option>
</select>
```

### Form Buttons
```html
<button class="ui-btn ui-btn-primary">Primary Button</button>
<button class="ui-btn ui-btn-ghost">Secondary Ghost</button>
<button class="ui-btn ui-btn-danger">Destructive Action</button>
<button class="ui-btn ui-btn-violet">Violet Action</button>
```

---

## 6. Data Representation

### Tables
Standard data tables wrapped in a scrolling helper to prevent container overflow.
```html
<div class="ui-table-wrap">
    <table class="ui-table">
        <thead>
            <tr>
                <th>Indicator</th>
                <th>Type</th>
                <th>Severity</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="mono cyan">192.168.1.100</td>
                <td class="mono muted">IP</td>
                <td><span class="ui-badge ui-badge-danger">CRITICAL</span></td>
            </tr>
        </tbody>
    </table>
</div>
```

### Progress & Activity Bars
Horizontal progress meters used to visualize volume, percentages, or timeline allocations.
```html
<div class="ui-bar-row">
    <div class="ui-bar-label">Indicator Matches</div>
    <div class="ui-bar-track">
        <div class="ui-bar-fill" style="width: 72%;"></div>
    </div>
    <div class="ui-bar-count">72%</div>
</div>
```

---

## 7. Statuses & Indicators

### Status Pills
```html
<!-- Live Status Indicator -->
<div class="ui-status-pill online">
    <span class="ui-pulse-dot"></span> LIVE MONITORING
</div>
```

### Badges
Small colored badges used to tag lists, table items, or server stats.
```html
<span class="ui-badge ui-badge-cyan">INFO</span>
<span class="ui-badge ui-badge-violet">MEDIUM</span>
<span class="ui-badge ui-badge-warning">HIGH</span>
<span class="ui-badge ui-badge-danger">CRITICAL</span>
<span class="ui-badge ui-badge-success">RESOLVED</span>
<span class="ui-badge ui-badge-muted">CLOSED</span>
```

---

## 8. Modals & Overlays

### Modal Overlay & Glass Dialog
Standard overlay container used to blur out the background workspace.
```html
<div class="modal-overlay" id="demoModal" style="display: none;">
    <div class="ui-glass-strong" style="max-width: 500px; width: 100%; padding: 1.75rem; border-radius: var(--ui-radius-lg);">
        <div class="ui-card-title" style="margin-bottom: 1.25rem;">
            <span>Add Indicator</span>
        </div>
        <form>
            <!-- Form fields -->
            <div style="display: flex; gap: 0.75rem; justify-content: flex-end; margin-top: 1.5rem;">
                <button type="button" class="ui-btn ui-btn-ghost" onclick="closeModal()">Cancel</button>
                <button type="submit" class="ui-btn ui-btn-primary">Submit</button>
            </div>
        </form>
    </div>
</div>
```

---

## 9. Empty States

Used inside lists, tables, or timeline visualizations when there is no data to display.
```html
<div class="ui-glass-card ui-bento-card ui-empty-state">
    <div class="ui-empty-icon">🛡️</div>
    <p class="ui-empty-text">No active assurance cases claims registered.</p>
</div>
```

---

## 10. Batch D Extensions

### Bento Card Auto-Sizer (`.ui-bento-card`)
Provides a flexible, minimum-height container matching grid components with custom hover effects.
```html
<div class="ui-glass-card ui-bento-card">
    <!-- Card Content -->
</div>
```

### Key-Value Stat Row (`.ui-stat-row`)
Draws inline key-value metrics with proper alignment, labels on the left, and values on the right.
```html
<div class="ui-stat-row">
    <span class="ui-stat-label">Encryption</span>
    <span class="ui-stat-value success">ENABLED</span>
</div>
```

### Section Heading (`.ui-section-heading`)
A clean, uppercase small divider line with bottom borders used to separate dashboard areas.
```html
<h2 class="ui-section-heading">Active Regressions</h2>
```

