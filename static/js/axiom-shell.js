/**
 * AXIOM Shell — Navigation & Interaction Engine
 * CTF Arena · EthicBids Technologies™
 * Version: 2.0.0
 *
 * Manages:
 * - Command Rail active state
 * - Context Sidebar open/close/pin
 * - Global Command Palette (Ctrl/Cmd+K)
 * - Topbar page title sync
 * - Mobile drawer
 * - Keyboard navigation
 */
(function () {
  'use strict';

  /* ── Constants ──────────────────────────────────────── */
  const SIDEBAR_COLLAPSED_KEY = 'ax_sidebar_collapsed';
  const SIDEBAR_PINNED_KEY    = 'ax_sidebar_pinned';

  /* ── DOM References ──────────────────────────────────── */
  const rail      = document.getElementById('ax-rail');
  const sidebar   = document.getElementById('ax-sidebar');
  const topbar    = document.getElementById('ax-topbar');
  const workspace = document.getElementById('ax-workspace');
  const overlay   = document.getElementById('ax-overlay');
  const palette   = document.getElementById('ax-palette');
  const paletteBd = document.getElementById('ax-palette-backdrop');
  const paletteIn = document.getElementById('ax-palette-input');

  /* ── Sidebar State ───────────────────────────────────── */
  let sidebarOpen   = false;
  let sidebarPinned = localStorage.getItem(SIDEBAR_PINNED_KEY) === '1';

  function openSidebar() {
    if (!sidebar) return;
    sidebarOpen = true;
    sidebar.classList.remove('collapsed');
    if (topbar)    topbar.classList.add('sidebar-open');
    if (workspace) workspace.classList.add('sidebar-open');
    if (overlay)   overlay.style.display = 'block';
    const colBtn = document.getElementById('ax-sidebar-collapse-btn');
    if (colBtn) colBtn.setAttribute('aria-expanded', 'true');
  }

  function closeSidebar() {
    if (!sidebar) return;
    sidebarOpen = false;
    sidebar.classList.add('collapsed');
    if (topbar)    topbar.classList.remove('sidebar-open');
    if (workspace) workspace.classList.remove('sidebar-open');
    if (overlay)   overlay.style.display = 'none';
    const colBtn = document.getElementById('ax-sidebar-collapse-btn');
    if (colBtn) colBtn.setAttribute('aria-expanded', 'false');
  }

  function toggleSidebar() {
    sidebarOpen ? closeSidebar() : openSidebar();
    if (sidebarPinned) {
      sidebarPinned = sidebarOpen;
      localStorage.setItem(SIDEBAR_PINNED_KEY, sidebarOpen ? '1' : '0');
    }
  }

  /* Restore pinned state */
  function initSidebarState() {
    const isMobile = window.innerWidth < 768;
    if (sidebarPinned && !isMobile) {
      openSidebar();
    } else {
      if (sidebar) sidebar.classList.add('collapsed');
    }
  }

  /* ── Command Rail Active State ──────────────────────── */
  function setRailActive() {
    const path = window.location.pathname;
    const railBtns = document.querySelectorAll('.ax-rail-btn[data-section]');
    railBtns.forEach(function (btn) {
      const section = btn.getAttribute('data-section');
      const active = path.startsWith(section) ||
                     (section === '/admin' && (path === '/admin' || path === '/admin/'));
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-current', active ? 'page' : 'false');
    });
  }

  /* ── Sidebar Active Nav Link ─────────────────────────── */
  function setSidebarActive() {
    const path = window.location.pathname;
    const links = document.querySelectorAll('.ax-sidebar-link[href]');
    links.forEach(function (link) {
      const href = link.getAttribute('href');
      const active = (href === path) ||
                     (href !== '/' && path.startsWith(href) && href.length > 1);
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'page');
    });
  }

  /* ── Public nav active state ─────────────────────────── */
  function setPublicNavActive() {
    const path = window.location.pathname;
    const links = document.querySelectorAll('.ax-public-nav-link[href]');
    links.forEach(function (link) {
      const href = link.getAttribute('href');
      const active = (href === path) ||
                     (href !== '/' && path.startsWith(href));
      link.classList.toggle('active', active);
    });
  }

  /* ── Breadcrumb & Topbar Title ───────────────────────── */
  function syncTopbarTitle() {
    const pageTitle = document.querySelector('[data-page-title]');
    const topbarTitle = document.getElementById('ax-topbar-title');
    if (pageTitle && topbarTitle) {
      topbarTitle.textContent = pageTitle.getAttribute('data-page-title') ||
                                pageTitle.textContent;
    }
  }

  /* ── Rail Section → Sidebar Panel switching ─────────── */
  function initRailSectionSwitch() {
    const railBtns = document.querySelectorAll('.ax-rail-btn[data-panel]');
    railBtns.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        const panelId = btn.getAttribute('data-panel');
        if (!panelId) return;
        const panels = document.querySelectorAll('.ax-sidebar-panel');
        panels.forEach(function (p) { p.hidden = true; });
        const target = document.getElementById(panelId);
        if (target) {
          target.hidden = false;
          // Update sidebar section title
          const label = btn.getAttribute('data-tooltip') || '';
          const titleEl = document.getElementById('ax-sidebar-section-title');
          if (titleEl) titleEl.textContent = label;
        }
        // Open sidebar if not open
        openSidebar();
      });
    });
  }

  /* ── Mobile hamburger ────────────────────────────────── */
  function initMobileHamburger() {
    const hamburger = document.getElementById('ax-hamburger');
    if (!hamburger) return;
    hamburger.addEventListener('click', toggleSidebar);
  }

  /* ── Sidebar collapse button ─────────────────────────── */
  function initCollapseBtn() {
    const btn = document.getElementById('ax-sidebar-collapse-btn');
    if (!btn) return;
    btn.addEventListener('click', function () {
      toggleSidebar();
    });
  }

  /* ── Sidebar pin button ──────────────────────────────── */
  function initPinBtn() {
    const btn = document.getElementById('ax-sidebar-pin-btn');
    if (!btn) return;
    btn.addEventListener('click', function () {
      sidebarPinned = !sidebarPinned;
      localStorage.setItem(SIDEBAR_PINNED_KEY, sidebarPinned ? '1' : '0');
      btn.classList.toggle('pinned', sidebarPinned);
      btn.setAttribute('aria-pressed', sidebarPinned.toString());
    });
    // Restore pin visual
    if (sidebarPinned) {
      btn.classList.add('pinned');
      btn.setAttribute('aria-pressed', 'true');
    }
  }

  /* ── Overlay click to close ──────────────────────────── */
  function initOverlay() {
    if (!overlay) return;
    overlay.addEventListener('click', function () {
      if (paletteBd && paletteBd.classList.contains('open')) {
        closePalette();
      } else {
        closeSidebar();
      }
    });
  }

  /* ── Command Palette ─────────────────────────────────── */
  const paletteItems = [
    /* Competition */
    { label: 'Dashboard',          desc: 'Admin control center',     href: '/admin',                        section: 'Competition', icon: 'dashboard' },
    { label: 'Challenges',         desc: 'Manage all challenges',    href: '/admin/challenges',             section: 'Competition', icon: 'flag' },
    { label: 'Categories',         desc: 'Challenge categories',     href: '/admin/categories',             section: 'Competition', icon: 'tag' },
    { label: 'Submissions',        desc: 'All flag submissions',     href: '/admin/submissions',            section: 'Competition', icon: 'inbox' },
    { label: 'Announcements',      desc: 'Post platform alerts',     href: '/admin/announcements',          section: 'Competition', icon: 'bell' },
    { label: 'Competition',        desc: 'Competition management',   href: '/admin/competition',            section: 'Competition', icon: 'trophy' },
    { label: 'Live Stats',         desc: 'Real-time metrics',        href: '/admin/competition/stats',      section: 'Competition', icon: 'chart' },
    /* Security */
    { label: 'SOC Center',         desc: 'Security operations',      href: '/admin/soc',                   section: 'Security', icon: 'shield' },
    { label: 'Threat Hunts',       desc: 'Hunt management',          href: '/admin/hunts',                 section: 'Security', icon: 'search' },
    { label: 'Threat Intelligence',desc: 'Intel feeds & indicators', href: '/admin/threat-intel',          section: 'Security', icon: 'radar' },
    { label: 'Incidents',          desc: 'Active incidents',         href: '/admin/cyberrange/incidents',  section: 'Security', icon: 'alert' },
    { label: 'Malware Analysis',   desc: 'Sample analysis lab',      href: '/admin/research/malware',      section: 'Security', icon: 'bug' },
    { label: 'Campaigns',          desc: 'Security campaigns',       href: '/admin/research/campaigns',    section: 'Security', icon: 'target' },
    { label: 'Cyber Range',        desc: 'Training environments',    href: '/admin/cyberrange',            section: 'Security', icon: 'globe' },
    /* Platform */
    { label: 'Mission Control',    desc: 'Platform convergence',     href: '/admin/mission-control',       section: 'Platform', icon: 'rocket' },
    { label: 'Organization',       desc: 'Team & org management',    href: '/admin/organization',          section: 'Platform', icon: 'building' },
    { label: 'Plugins',            desc: 'Plugin marketplace',       href: '/admin/plugins',               section: 'Platform', icon: 'plug' },
    { label: 'Users',              desc: 'User management',          href: '/admin/users',                 section: 'Platform', icon: 'users' },
    { label: 'AI Services',        desc: 'AI/ML service status',     href: '/admin/ai',                   section: 'Platform', icon: 'cpu' },
    /* Governance */
    { label: 'Compliance',         desc: 'Compliance controls',      href: '/admin/compliance',            section: 'Governance', icon: 'check-circle' },
    { label: 'Risk Quantification',desc: 'Risk analysis & scoring',  href: '/admin/risk-quantification',   section: 'Governance', icon: 'activity' },
    { label: 'Resilience Center',  desc: 'Resilience posture',       href: '/admin/resilience-center',    section: 'Governance', icon: 'anchor' },
    { label: 'Governance',         desc: 'Policy governance',        href: '/admin/governance',           section: 'Governance', icon: 'book' },
    /* Public */
    { label: 'Scoreboard',         desc: 'Public leaderboard',       href: '/scoreboard',                  section: 'Public', icon: 'list' },
    { label: 'Challenges (Public)',desc: 'Participant challenge view',href: '/',                            section: 'Public', icon: 'grid' },
  ];

  let paletteFiltered = paletteItems.slice();
  let paletteFocused = -1;
  let paletteOpen = false;

  function openPalette() {
    if (!paletteBd || !paletteIn) return;
    paletteOpen = true;
    paletteBd.classList.add('open');
    paletteIn.value = '';
    paletteFocused = -1;
    renderPaletteResults(paletteItems);
    setTimeout(function () { paletteIn.focus(); }, 50);
    document.body.style.overflow = 'hidden';
  }

  function closePalette() {
    if (!paletteBd) return;
    paletteOpen = false;
    paletteBd.classList.remove('open');
    document.body.style.overflow = '';
  }

  function renderPaletteResults(items) {
    const container = document.getElementById('ax-palette-results');
    if (!container) return;
    container.innerHTML = '';
    paletteFocused = -1;

    if (items.length === 0) {
      container.innerHTML =
        '<div style="padding:2rem;text-align:center;color:var(--ax-text-muted);font-size:var(--ax-text-sm);">No results found</div>';
      return;
    }

    // Group by section
    const sections = {};
    items.forEach(function (item) {
      if (!sections[item.section]) sections[item.section] = [];
      sections[item.section].push(item);
    });

    Object.keys(sections).forEach(function (section) {
      const label = document.createElement('div');
      label.className = 'ax-palette-section-label';
      label.textContent = section;
      container.appendChild(label);

      sections[section].forEach(function (item, localIdx) {
        const a = document.createElement('a');
        a.href = item.href;
        a.className = 'ax-palette-item';
        a.setAttribute('data-palette-index', container.querySelectorAll('.ax-palette-item').length);
        a.innerHTML =
          '<div class="ax-palette-item-icon">' + getPaletteIcon(item.icon) + '</div>' +
          '<div class="ax-palette-item-content">' +
            '<div class="ax-palette-item-label">' + escHtml(item.label) + '</div>' +
            '<div class="ax-palette-item-desc">' + escHtml(item.desc) + '</div>' +
          '</div>';
        a.addEventListener('click', function () { closePalette(); });
        container.appendChild(a);
      });
    });
  }

  function filterPalette(query) {
    if (!query.trim()) {
      renderPaletteResults(paletteItems);
      return;
    }
    const q = query.toLowerCase();
    const results = paletteItems.filter(function (item) {
      return item.label.toLowerCase().includes(q) ||
             item.desc.toLowerCase().includes(q) ||
             item.section.toLowerCase().includes(q);
    });
    renderPaletteResults(results);
  }

  function movePaletteFocus(dir) {
    const items = document.querySelectorAll('.ax-palette-item');
    if (!items.length) return;
    items.forEach(function (el) { el.classList.remove('focused'); });
    paletteFocused = Math.max(0, Math.min(items.length - 1, paletteFocused + dir));
    items[paletteFocused].classList.add('focused');
    items[paletteFocused].scrollIntoView({ block: 'nearest' });
  }

  function selectFocusedPaletteItem() {
    const item = document.querySelector('.ax-palette-item.focused');
    if (item) {
      closePalette();
      window.location.href = item.href;
    }
  }

  function initPalette() {
    if (!paletteBd || !paletteIn) return;

    // Close on backdrop click
    paletteBd.addEventListener('click', function (e) {
      if (e.target === paletteBd) closePalette();
    });

    // Input filter
    paletteIn.addEventListener('input', function () {
      filterPalette(paletteIn.value);
    });

    // Keyboard nav within palette
    paletteIn.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); movePaletteFocus(1); }
      if (e.key === 'ArrowUp')   { e.preventDefault(); movePaletteFocus(-1); }
      if (e.key === 'Enter')     { e.preventDefault(); selectFocusedPaletteItem(); }
      if (e.key === 'Escape')    { closePalette(); }
    });
  }

  /* ── Global keyboard shortcuts ───────────────────────── */
  function initKeyboardShortcuts() {
    document.addEventListener('keydown', function (e) {
      // Cmd/Ctrl + K — Command Palette
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        paletteOpen ? closePalette() : openPalette();
        return;
      }
      // Escape — close palette or sidebar
      if (e.key === 'Escape') {
        if (paletteOpen) { closePalette(); return; }
        if (sidebarOpen && !sidebarPinned) { closeSidebar(); }
      }
    });

    // Palette trigger button
    const paletteTrigger = document.getElementById('ax-palette-trigger');
    if (paletteTrigger) {
      paletteTrigger.addEventListener('click', function () {
        paletteOpen ? closePalette() : openPalette();
      });
    }
  }

  /* ── Topbar scroll shadow ────────────────────────────── */
  function initTopbarScroll() {
    if (!topbar) return;
    window.addEventListener('scroll', function () {
      topbar.style.boxShadow = window.scrollY > 4
        ? 'var(--ax-shadow-sm)'
        : 'none';
    }, { passive: true });
  }

  /* ── Sidebar overlay (mobile) ────────────────────────── */
  function initSidebarOverlay() {
    const sidebarOverlay = document.getElementById('ax-sidebar-overlay');
    if (!sidebarOverlay) return;
    sidebarOverlay.addEventListener('click', function () {
      closeSidebar();
    });
  }

  /* ── Auto-collapse sidebar on narrow resize ──────────── */
  function initResponsive() {
    window.addEventListener('resize', function () {
      if (window.innerWidth < 768 && sidebarOpen) {
        closeSidebar();
      }
    }, { passive: true });
  }

  /* ── Chart.js AXIOM theme ────────────────────────────── */
  window.AXIOM_CHART_DEFAULTS = {
    color: '#8FA8C2',
    font: { family: "'Inter', system-ui, sans-serif", size: 11 },
    grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
    tick: { color: '#5A7490' },
    barColor:      'rgba(59, 125, 216, 0.7)',
    barColorHover: 'rgba(59, 125, 216, 0.9)',
    lineColor:     '#3B7DD8',
    areaFill:      'rgba(59, 125, 216, 0.08)',
    greenBar:      'rgba(42, 157, 111, 0.7)',
    redBar:        'rgba(196, 50, 50, 0.7)',
    purpleBar:     'rgba(120, 82, 204, 0.7)',
    amberBar:      'rgba(200, 137, 10, 0.7)',
  };

  function applyChartDefaults() {
    if (typeof Chart === 'undefined') return;
    Chart.defaults.color = '#8FA8C2';
    Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
    Chart.defaults.font.size = 11;
    Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';
    Chart.defaults.plugins.legend.display = false;
    Chart.defaults.plugins.tooltip.backgroundColor = '#111622';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(255,255,255,0.09)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.titleColor = '#E2EAF4';
    Chart.defaults.plugins.tooltip.bodyColor = '#8FA8C2';
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
    Chart.defaults.scale.grid.color = 'rgba(255,255,255,0.05)';
    Chart.defaults.scale.ticks.color = '#5A7490';
    Chart.defaults.elements.bar.borderRadius = 3;
    Chart.defaults.elements.bar.borderSkipped = false;
    Chart.defaults.elements.line.tension = 0.3;
    Chart.defaults.elements.line.borderWidth = 2;
    Chart.defaults.elements.point.radius = 3;
    Chart.defaults.elements.point.hoverRadius = 5;
  }

  /* ── Sidebar mouse-enter/leave hover logic ───────────── */
  function initSidebarHover() {
    if (!rail || !sidebar || window.innerWidth < 768) return;
    // Hover open if not pinned
    rail.addEventListener('mouseenter', function () {
      if (!sidebarPinned) openSidebar();
    });

    const shellEl = document.getElementById('ax-shell');
    if (!shellEl) return;
    shellEl.addEventListener('mouseleave', function () {
      if (!sidebarPinned) closeSidebar();
    });
  }

  /* ── Helpers ─────────────────────────────────────────── */
  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function getPaletteIcon(name) {
    const icons = {
      dashboard:     '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"/></svg>',
      flag:          '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3 3v18m0-15.75l4.5-2.25 4.5 2.25 4.5-2.25 4.5 2.25V15l-4.5-2.25L12 15l-4.5-2.25L3 15"/></svg>',
      tag:           '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z"/><path stroke-linecap="round" stroke-linejoin="round" d="M6 6h.008v.008H6V6z"/></svg>',
      inbox:         '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 012.012 1.244l.256.512a2.25 2.25 0 002.013 1.244h3.218a2.25 2.25 0 002.013-1.244l.256-.512a2.25 2.25 0 012.013-1.244h3.859m-19.5.338V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 00-2.15-1.588H6.911a2.25 2.25 0 00-2.15 1.588L2.35 13.177a2.25 2.25 0 00-.1.661z"/></svg>',
      bell:          '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"/></svg>',
      trophy:        '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M7.73 9.728a6.726 6.726 0 002.748 1.35m8.272-6.842V4.5c0 2.108-.966 3.99-2.48 5.228m2.48-5.492a46.32 46.32 0 012.916.52 6.003 6.003 0 01-5.395 4.972m0 0a6.726 6.726 0 01-2.749 1.35m0 0a6.772 6.772 0 01-3.044 0"/></svg>',
      chart:         '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"/></svg>',
      shield:        '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"/></svg>',
      search:        '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803 7.5 7.5 0 0015.803 15.803z"/></svg>',
      radar:         '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z"/></svg>',
      alert:         '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/></svg>',
      bug:           '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 12.75c1.148 0 2.278.08 3.383.237 1.037.146 1.866.966 1.866 2.013 0 3.728-2.35 6.75-5.25 6.75S6.75 18.728 6.75 15c0-1.046.83-1.867 1.866-2.013A24.204 24.204 0 0112 12.75zm0 0V8.25m0 0a.75.75 0 01-.75-.75V6a2.25 2.25 0 014.5 0v1.5a.75.75 0 01-.75.75m-3 0h3m-1.5-3.75V2.25m0 0h3m-3 0h-3m3 3.75V2.25"/></svg>',
      target:        '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M7.864 4.243A7.5 7.5 0 0119.5 10.5c0 2.92-.556 5.709-1.568 8.268M5.742 6.364A7.465 7.465 0 004.5 10.5a7.464 7.464 0 01-1.15 3.993m1.989 3.559A11.209 11.209 0 008.25 10.5a3.75 3.75 0 117.5 0 11.21 11.21 0 01-2.589 7.052m-5.421-.001A11.25 11.25 0 016.5 10.5H5.25A11.25 11.25 0 004.5 14.25"/></svg>',
      globe:         '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418"/></svg>',
      rocket:        '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z"/></svg>',
      building:      '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z"/></svg>',
      plug:          '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 16.875h3.375m0 0h3.375m-3.375 0V13.5m0 3.375v3.375M6 10.5h2.25a2.25 2.25 0 002.25-2.25V6a2.25 2.25 0 00-2.25-2.25H6A2.25 2.25 0 003.75 6v2.25A2.25 2.25 0 006 10.5zm0 9.75h2.25A2.25 2.25 0 0010.5 18v-2.25a2.25 2.25 0 00-2.25-2.25H6a2.25 2.25 0 00-2.25 2.25V18A2.25 2.25 0 006 20.25zm9.75-9.75H18a2.25 2.25 0 002.25-2.25V6A2.25 2.25 0 0018 3.75h-2.25A2.25 2.25 0 0013.5 6v2.25a2.25 2.25 0 002.25 2.25z"/></svg>',
      users:         '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"/></svg>',
      cpu:           '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 002.25-2.25V6.75a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6.75v10.5a2.25 2.25 0 002.25 2.25zm.75-12h9v9h-9v-9z"/></svg>',
      'check-circle':'<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
      activity:      '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"/></svg>',
      anchor:        '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z"/></svg>',
      book:          '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"/></svg>',
      list:          '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zM3.75 12h.007v.008H3.75V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm-.375 5.25h.007v.008H3.75v-.008zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"/></svg>',
      grid:          '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"/></svg>',
    };
    return icons[name] || icons['grid'];
  }

  /* ── Init ────────────────────────────────────────────── */
  function init() {
    initSidebarState();
    setRailActive();
    setSidebarActive();
    setPublicNavActive();
    syncTopbarTitle();
    initRailSectionSwitch();
    initMobileHamburger();
    initCollapseBtn();
    initPinBtn();
    initOverlay();
    initPalette();
    initKeyboardShortcuts();
    initTopbarScroll();
    initSidebarOverlay();
    initResponsive();
    initSidebarHover();
    applyChartDefaults();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
