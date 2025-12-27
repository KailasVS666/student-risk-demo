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
  const htmlEl = document.documentElement;
  const bodyEl = document.body;
  
  if (theme === 'dark') {
    htmlEl.classList.add('dark');
    bodyEl.classList.add('dark:bg-gray-900');
  } else {
    htmlEl.classList.remove('dark');
    bodyEl.classList.remove('dark:bg-gray-900');
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
    // Use arrow function to preserve context
    themeToggle.addEventListener('click', (e) => {
      e.preventDefault();
      toggleTheme();
    });
    console.log('Theme toggle handler attached');
  } else {
    console.warn('Theme toggle button not found');
  }
}

// Initialize theme on module load
initTheme();
