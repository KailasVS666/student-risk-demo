/**
 * Theme Management Module
 * Handles dark mode toggle and persistence.
 */

import APP_CONFIG from './config.js';

/**
 * Initializes theme based on saved preference.
 */
export function initTheme() {
  // Force dark theme for single-theme experience
  localStorage.setItem(APP_CONFIG.THEME_KEY, 'dark');
  applyTheme('dark');
  updateThemeIcon('dark');
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
 * Updates theme toggle icon.
 * @param {string} theme - Current theme
 */
function updateThemeIcon(theme) {
  const lightIcon = document.getElementById('themeIconLight');
  const darkIcon = document.getElementById('themeIconDark');
  
  if (lightIcon && darkIcon) {
    if (theme === 'dark') {
      lightIcon.classList.remove('hidden');
      darkIcon.classList.add('hidden');
    } else {
      lightIcon.classList.add('hidden');
      darkIcon.classList.remove('hidden');
    }
  }
}

/**
 * Toggles between light and dark themes.
 */
export function toggleTheme() {
  // Dark-only mode: no toggle behavior
  localStorage.setItem(APP_CONFIG.THEME_KEY, 'dark');
  applyTheme('dark');
  updateThemeIcon('dark');
}

/**
 * Sets up theme toggle button event listener.
 */
export function setupThemeToggle() {
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    // Hide or disable the toggle since only dark mode is supported now
    themeToggle.setAttribute('aria-hidden', 'true');
    themeToggle.setAttribute('tabindex', '-1');
    themeToggle.style.display = 'none';
  } else {
    console.warn('Theme toggle button not found');
  }
}

// Initialize theme on module load
initTheme();
