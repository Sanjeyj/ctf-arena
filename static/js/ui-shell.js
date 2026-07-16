/**
 * Cyber Defense Platform — UI Shell
 * Handles sidebar collapse/expand, mobile drawer, topbar sync.
 * Version: 1.0.0 (Batch A)
 */
(function () {
  'use strict';

  /* ── Sidebar state keys ─────────────────────────────── */
  var SIDEBAR_KEY = 'cdp_sidebar_collapsed';

  /* ── DOM refs (resolved after DOMContentLoaded) ────── */
  var sidebar, topbar, workspace, toggleBtn, overlay;

  /* ── Utility ─────────────────────────────────────────── */
  function isMobile() {
    return window.innerWidth <= 768;
  }

  /* ── Apply sidebar state ────────────────────────────── */
  function applySidebarState(collapsed, animate) {
    if (!sidebar) return;

    if (isMobile()) {
      // On mobile: collapsed = drawer closed, !collapsed = drawer open
      sidebar.classList.toggle('mobile-open', !collapsed);
      if (overlay) overlay.classList.toggle('active', !collapsed);
      if (topbar) topbar.classList.remove('sidebar-collapsed');
      if (workspace) workspace.classList.remove('sidebar-collapsed');
      if (toggleBtn) {
        toggleBtn.setAttribute('aria-expanded', String(!collapsed));
      }
    } else {
      sidebar.classList.toggle('collapsed', collapsed);
      if (topbar) topbar.classList.toggle('sidebar-collapsed', collapsed);
      if (workspace) workspace.classList.toggle('sidebar-collapsed', collapsed);
      if (toggleBtn) {
        toggleBtn.setAttribute('aria-expanded', String(!collapsed));
      }
      // Persist preference
      try { localStorage.setItem(SIDEBAR_KEY, collapsed ? '1' : '0'); } catch (e) {}
    }
  }

  /* ── Toggle sidebar ─────────────────────────────────── */
  function toggleSidebar() {
    if (!sidebar) return;
    if (isMobile()) {
      var isOpen = sidebar.classList.contains('mobile-open');
      applySidebarState(isOpen); // close if open, open if closed
    } else {
      var isCollapsed = sidebar.classList.contains('collapsed');
      applySidebarState(!isCollapsed);
    }
  }

  /* ── Active link detection ──────────────────────────── */
  function markActiveLink() {
    var path = window.location.pathname;
    var links = sidebar ? sidebar.querySelectorAll('.sidebar-link') : [];
    links.forEach(function (link) {
      var href = link.getAttribute('href') || '';
      if (href && href !== '#') {
        var isActive = path === href || path.startsWith(href + '/');
        link.classList.toggle('active', isActive);
        if (isActive) {
          link.setAttribute('aria-current', 'page');
        } else {
          link.removeAttribute('aria-current');
        }
      }
    });
  }

  /* ── Init ───────────────────────────────────────────── */
  function init() {
    sidebar   = document.getElementById('admin-sidebar');
    topbar    = document.querySelector('.ui-topbar');
    workspace = document.querySelector('.ui-workspace');
    toggleBtn = document.getElementById('sidebar-toggle');
    overlay   = document.getElementById('sidebar-overlay');

    if (!sidebar) return; // Not an admin page

    // Restore desktop preference
    if (!isMobile()) {
      var pref;
      try { pref = localStorage.getItem(SIDEBAR_KEY); } catch (e) {}
      if (pref === '1') {
        applySidebarState(true, false);
      }
    }

    // Toggle button
    if (toggleBtn) {
      toggleBtn.addEventListener('click', toggleSidebar);
    }

    // Close on overlay click (mobile)
    if (overlay) {
      overlay.addEventListener('click', function () {
        applySidebarState(true);
      });
    }

    // Close mobile drawer on nav link click
    sidebar.querySelectorAll('.sidebar-link').forEach(function (link) {
      link.addEventListener('click', function () {
        if (isMobile()) applySidebarState(true);
      });
    });

    // Keyboard: Escape closes mobile drawer
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && isMobile() && sidebar.classList.contains('mobile-open')) {
        applySidebarState(true);
        if (toggleBtn) toggleBtn.focus();
      }
    });

    // Resize: reset mobile state
    window.addEventListener('resize', function () {
      if (!isMobile()) {
        sidebar.classList.remove('mobile-open');
        if (overlay) overlay.classList.remove('active');
      }
    });

    markActiveLink();
  }

  document.addEventListener('DOMContentLoaded', init);

})();
