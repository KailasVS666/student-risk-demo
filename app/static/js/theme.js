/**
 * Theme Management Module
 * Handles dark mode toggle and persistence.
 */

import APP_CONFIG from './config.js';

/**
 * Initializes theme based on saved preference.
 */
export function initTheme() {
  const savedTheme = localStorage.getItem(APP_CONFIG.THEME_KEY) || 'light';
  applyTheme(savedTheme);
  updateThemeIcon(savedTheme);
}

/**
 * Applies the specified theme.
 * @param {string} theme - 'light' or 'dark'
 */
export function applyTheme(theme) {
  if (theme === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
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
  const currentTheme = localStorage.getItem(APP_CONFIG.THEME_KEY) || 'light';
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  
  localStorage.setItem(APP_CONFIG.THEME_KEY, newTheme);
  applyTheme(newTheme);
  updateThemeIcon(newTheme);
}

/**
 * Sets up theme toggle button event listener.
 */
export function setupThemeToggle() {
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
  }
}

// Initialize theme on module load
initTheme();
