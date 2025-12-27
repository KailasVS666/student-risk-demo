/**
 * Theme Management Module
 * Dark-only: apply and persist dark mode.
 */

import APP_CONFIG from './config.js';

/**
 * Initializes theme based on saved preference.
 */
export function initTheme() {
  // Force dark theme for single-theme experience
  try { localStorage.setItem(APP_CONFIG.THEME_KEY, 'dark'); } catch {}
  applyTheme('dark');
}

/**
 * Applies the specified theme.
 * @param {string} theme - 'light' or 'dark'
 */
export function applyTheme(theme) {
  const htmlEl = document.documentElement;

  if (theme === 'dark') {
    htmlEl.classList.add('dark');
  } else {
    htmlEl.classList.remove('dark');
  }
}

/**
 * Maintains API parity with previous toggle behavior while keeping dark-only.
 * We simply ensure the theme is initialized and hide any toggle control if present.
 */
export function setupThemeToggle() {
  initTheme();

  const toggleEl = document.getElementById('themeToggle');
  if (toggleEl) {
    toggleEl.classList.add('hidden');
    toggleEl.setAttribute('aria-hidden', 'true');
  }
}

// Initialize theme on module load
initTheme();
