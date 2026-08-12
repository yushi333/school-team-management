/**
 * ACM 校队管理系统 — Dark Mode Toggle
 */
(function () {
    const STORAGE_KEY = 'acm-team-theme';
    const DARK = 'dark';
    const LIGHT = 'light';

    function getSavedTheme() {
        try { return localStorage.getItem(STORAGE_KEY); } catch (e) { return null; }
    }
    function saveTheme(t) {
        try { localStorage.setItem(STORAGE_KEY, t); } catch (e) { /* quota or private browsing */ }
    }

    function applyTheme(theme) {
        if (theme === DARK) {
            document.documentElement.setAttribute('data-bs-theme', DARK);
        } else {
            document.documentElement.removeAttribute('data-bs-theme');
        }
    }

    // ---- Boot: apply saved or OS preference immediately (prevents FOUC) ----
    const saved = getSavedTheme();
    if (saved) {
        applyTheme(saved);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        applyTheme(DARK);
    }

    // ---- Toggle button ----
    function updateToggleIcon(btn, theme) {
        const icon = btn.querySelector('i');
        if (!icon) return;
        if (theme === DARK) {
            icon.className = 'bi bi-sun-fill';
            btn.setAttribute('title', '切换到日间模式');
        } else {
            icon.className = 'bi bi-moon-fill';
            btn.setAttribute('title', '切换到夜间模式');
        }
    }

    function initToggle() {
        const btn = document.getElementById('theme-toggle');
        if (!btn) return;

        const current = document.documentElement.hasAttribute('data-bs-theme') ? DARK : LIGHT;
        updateToggleIcon(btn, current);

        btn.addEventListener('click', function () {
            const now = document.documentElement.hasAttribute('data-bs-theme') ? DARK : LIGHT;
            const next = now === DARK ? LIGHT : DARK;
            applyTheme(next);
            saveTheme(next);
            updateToggleIcon(btn, next);
        });
    }

    // Listen for OS preference changes (only when user hasn't manually set)
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
            if (getSavedTheme() === null) {
                applyTheme(e.matches ? DARK : LIGHT);
                const btn = document.getElementById('theme-toggle');
                if (btn) updateToggleIcon(btn, e.matches ? DARK : LIGHT);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initToggle);
    } else {
        initToggle();
    }
})();
