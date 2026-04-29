/**
 * SPARS — Core Application JavaScript
 * Sidebar toggle, animated counters, keyboard shortcuts, active link detection
 */
(function () {
    'use strict';

    /* ================================================================
       SIDEBAR TOGGLE (MOBILE)
       ================================================================ */
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.sidebar-toggle');
    const overlay = document.querySelector('.sidebar-overlay');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            overlay && overlay.classList.toggle('open');
        });

        overlay && overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('open');
        });
    }

    /* ================================================================
       ANIMATED NUMBER COUNTERS
       ================================================================ */
    function animateCounters() {
        document.querySelectorAll('[data-counter]').forEach(el => {
            const target = parseFloat(el.textContent);
            if (isNaN(target)) return;

            const suffix = el.dataset.suffix || '';
            const duration = 900;
            const start = performance.now();

            el.textContent = '0' + suffix;

            function step(now) {
                const elapsed = now - start;
                const progress = Math.min(elapsed / duration, 1);
                // ease-out cubic
                const eased = 1 - Math.pow(1 - progress, 3);
                const current = Number.isInteger(target)
                    ? Math.round(eased * target)
                    : (eased * target).toFixed(2);
                el.textContent = current + suffix;
                if (progress < 1) requestAnimationFrame(step);
            }

            requestAnimationFrame(step);
        });
    }

    // Run counters when page loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', animateCounters);
    } else {
        animateCounters();
    }

    /* ================================================================
       ACTIVE NAV LINK DETECTION
       ================================================================ */
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href && href !== '#' && href !== '/logout') {
            if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
                link.classList.add('active');
            }
        }
    });

    /* ================================================================
       KEYBOARD SHORTCUTS
       ================================================================ */
    const shortcutsOverlay = document.getElementById('shortcuts-overlay');

    document.addEventListener('keydown', function (e) {
        // Don't trigger when typing in inputs
        if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName) || e.target.isContentEditable) {
            if (e.key === 'Escape') e.target.blur();
            return;
        }

        // ? — Show shortcuts overlay
        if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            if (shortcutsOverlay) {
                shortcutsOverlay.classList.toggle('visible');
            }
        }

        // Escape — Close shortcuts overlay
        if (e.key === 'Escape') {
            if (shortcutsOverlay) shortcutsOverlay.classList.remove('visible');
        }

        // / — Focus search
        if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
            const searchInput = document.querySelector('.table-search input') ||
                                document.querySelector('input[name="search"]') ||
                                document.querySelector('input[type="text"]');
            if (searchInput) {
                e.preventDefault();
                searchInput.focus();
            }
        }

        // Ctrl+P — Print
        if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
            e.preventDefault();
            window.print();
        }

        // Ctrl+E — Toggle edit mode
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            const editBtn = document.getElementById('edit-mode-toggle');
            if (editBtn) {
                e.preventDefault();
                editBtn.click();
            }
        }
    });

    // Close shortcuts overlay on click
    if (shortcutsOverlay) {
        shortcutsOverlay.addEventListener('click', function (e) {
            if (e.target === shortcutsOverlay) {
                shortcutsOverlay.classList.remove('visible');
            }
        });
    }

})();
