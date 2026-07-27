# AXIOM Design System Specifications
**Version:** 2.0.0 (AXIOM Core)
**CSS Asset:** [axiom.css](file:///d:/CTFd/CTF/ctf-arena/static/css/axiom.css)
**JS Asset:** [axiom-shell.js](file:///d:/CTFd/CTF/ctf-arena/static/js/axiom-shell.js)

---

## 1. Design Philosophy

AXIOM is a precise, purposeful design language engineered specifically for security operations and cyber defense software. It favors data clarity over decoration, hierarchy over complexity, and usability over flashiness.

### Principles:
1. **Negative Space is Signal**: Negative space is not empty; it is breathing room that separates distinct streams of threat data.
2. **Density Without Noise**: Dashboard cards contain detailed telemetry, but high alignment and layout grid alignment keep it legible.
3. **Color = Meaning**: Color is reserved for status indication and primary actions. If everything stands out, nothing does.
4. **Typography Creates Hierarchy**: High-contrast size scale and monospace font formatting demarcate headings, telemetry values, and regular labels.
5. **Motion Reveals Structure**: Transitions are physical: panels slide in to reveal context, command palettes scale from the center of attention.

---

## 2. Core Tokens (Colors, Type, Motion)

All tokens are defined as CSS Custom Properties in `:root` inside `axiom.css`.

### 2.1 Color Palette

#### Surface Scale:
- `--ax-bg-base`: `#070910` (Main background)
- `--ax-bg-surface`: `#0D1018` (Rail, sidebar, topbar backgrounds)
- `--ax-bg-elevated`: `#111622` (Card surface)
- `--ax-bg-component`: `#16202E` (Inputs, inner card containers)
- `--ax-bg-hover`: `#1C2A3A` (Component hover state)
- `--ax-bg-active`: `#223244` (Component active/pressed state)

#### Text Scale:
- `--ax-text-primary`: `#E2EAF4` (High contrast text)
- `--ax-text-secondary`: `#8FA8C2` (Labels and metadata)
- `--ax-text-muted`: `#5A7490` (Placeholders and hint text)
- `--ax-text-disabled`: `#374D62` (Disabled states)
- `--ax-text-blue`: `#3B7DD8` / `#5B9BE8` (Actionable text/links)

#### Semantics (Status Indicators):
- **Blue (Info/Active)**: `--ax-blue` (`#3B7DD8`), `--ax-blue-bright` (`#5B9BE8`)
- **Green (Success/Healthy)**: `--ax-green` (`#2A9D6F`), `--ax-green-bright` (`#38C48C`)
- **Amber (Warning/Degraded)**: `--ax-amber` (`#C8890A`), `--ax-amber-bright` (`#E8A020`)
- **Red (Critical/Failed)**: `--ax-red` (`#C43232`), `--ax-red-bright` (`#E04444`)
- **Purple (AI/Intel/Intelligence)**: `--ax-purple` (`#7852CC`), `--ax-purple-bright` (`#9470E8`)

### 2.2 Typography
- **Primary Typeface**: `Inter` (sans-serif) for titles, menus, and copy.
- **Data/Code Typeface**: `JetBrains Mono` (monospace) for scores, ranks, timestamps, and codes.
- **Type Scale**:
  - `32px` (`--ax-text-3xl`)
  - `24px` (`--ax-text-2xl`)
  - `20px` (`--ax-text-xl`)
  - `16px` (`--ax-text-lg`)
  - `14px` (`--ax-text-md`)
  - `13px` (`--ax-text-base`) - Main body copy baseline
  - `12px` (`--ax-text-sm`)
  - `11px` (`--ax-text-xs`)
  - `10px` (`--ax-text-2xs`) - Badges and secondary counts

### 2.3 Spacing
Based on a clean `4px` grid:
- `--ax-space-1`: `4px`
- `--ax-space-2`: `8px`
- `--ax-space-3`: `12px`
- `--ax-space-4`: `16px`
- `--ax-space-5`: `20px`
- `--ax-space-6`: `24px`
- `--ax-space-8`: `32px`
- `--ax-space-12`: `48px`
- `--ax-space-14`: `56px`

---

## 3. Application Shell Structure

The admin workspace operates as a dual-navigation layout system:

- **Command Rail (`.ax-rail`)**:
  - Permanent vertical navigation bar pinned to the left edge of the viewport.
  - **Width**: `56px`
  - Holds category selector icons (e.g., Competition, Security Operations, Governance, Platform Settings).
  - Mouse-enter or clicking any button slides open the Context Sidebar.

- **Context Sidebar (`.ax-sidebar`)**:
  - Holds secondary, section-specific navigation items.
  - **Width**: `220px`
  - Slides out from behind the rail when a section is active or hovered.
  - Can be pinned permanently to create a split navigation layout. State is saved automatically to localStorage under the key `ax_sidebar_pinned`.

- **Command Palette (`.ax-palette`)**:
  - Instantly activated using `Ctrl + K` or `Cmd + K`.
  - Provides quick-jump keyboard-driven navigation across all competition screens.
  - Search filtering, scroll navigation using arrow keys, and execution using Enter are handled in `axiom-shell.js`.

---

## 4. Components Specifications

### 4.1 Cards (`.ax-card`)
- Built-in borders and subtle drop-shadows.
- Supports semantic accent colored borders at the top edge using:
  - `.ax-card-accent-blue`
  - `.ax-card-accent-green`
  - `.ax-card-accent-amber`
  - `.ax-card-accent-red`
  - `.ax-card-accent-purple`

### 4.2 KPI Metric Tiles (`.ax-metric`)
- Highlights numbers or telemetry.
- Utilizes JetBrains Mono for the number block, sized up to `32px`.
- Composed of:
  - `.ax-metric-label`
  - `.ax-metric-value`
  - `.ax-metric-sub`
  - `.ax-metric-delta` (shows percentage adjustments with up/down arrows)

### 4.3 Table System (`.ax-table`)
- Custom scrolling container (`.ax-table-wrap`) to prevent bleed.
- Fixed table columns, headers stay sticky at the top when scrolling, rows hover with smooth `.ax-bg-hover` transitions.
- Supports `.ax-table-mono` for cells showing hex codes, IDs, or timestamps.

---

## 5. Motion and Interactions

All transition effects are governed by centralized easing variables:
- **Slide Transitions**: `var(--ax-ease-out)` (duration `180ms` for navigation sidebar slide-out).
- **Hover Transitions**: `var(--ax-ease-out)` (duration `100ms` for color changes, active rail highlight).
- **Scale Transitions**: `var(--ax-ease-spring)` (duration `200ms` for command palette bounce-up).

---

## 6. Accessibility Standards

1. **Focus Rings**: Focus-visible rings are configured with a `2px` solid `--ax-blue` outline and `2px` offset.
2. **Reduced Motion**: Under `@media (prefers-reduced-motion: reduce)`, all transitions, slide animations, and scale transforms are set to `0ms` to prevent motion sickness.
3. **High Contrast**: Special forced-colors overrides are included to apply clear borders to cards and panels when system high contrast mode is active.
4. **Keyboard Friendly**: Screen elements like the Command Palette and Context Sidebar can be fully operated using standard keyboard layouts (`Tab`, `Arrow keys`, `Enter`, `Escape`).
