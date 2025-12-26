/**
 * UI/UX Utility Functions
 * Provides common UI operations like toasts, button loading states, and DOM helpers.
 */

import APP_CONFIG from './config.js';

/**
 * Shows a temporary, non-intrusive toast notification.
 * @param {string} message - The message to display.
 * @param {('success'|'error'|'info')} [type='info'] - The type of toast notification.
 * @example
 * showToast('Profile saved successfully!', 'success');
 */
export function showToast(message, type = 'info') {
  const toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    console.warn('Toast container not found in DOM');
    return;
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'polite');

  toastContainer.appendChild(toast);
  
  // Trigger animation
  setTimeout(() => {
    toast.classList.add('show');
  }, 10);

  // Hide and remove after 3 seconds
  setTimeout(() => {
    toast.classList.remove('show');
    toast.addEventListener('transitionend', () => toast.remove(), { once: true });
  }, 3000);
}

/**
 * Manages the loading state of a button during async operations.
 * @param {HTMLElement} button - The button element to manage.
 * @param {boolean} isLoading - True to show spinner and disable, false to restore.
 * @param {string} [originalText='Submit'] - The original button text to restore.
 * @example
 * setButtonLoading(button, true, 'Generate Advice');
 * // ... async work ...
 * setButtonLoading(button, false, 'Generate Advice');
 */
export function setButtonLoading(button, isLoading, originalText = 'Submit') {
  if (!button) return;

  button.disabled = isLoading;
  button.dataset.originalText = originalText;

  if (isLoading) {
    const isGenerateBtn = button.id === 'generateAdviceBtn';
    const loadingText = isGenerateBtn ? APP_CONFIG.BUTTON_TEXT.ANALYZING : APP_CONFIG.BUTTON_TEXT.LOADING;
    button.innerHTML = `<span class="button-loader"></span>${loadingText}`;
  } else {
    button.innerHTML = button.dataset.originalText || originalText;
  }
}

/**
 * Adds a visible error message to a form field.
 * @param {HTMLElement} inputEl - The input element to mark as errored.
 * @param {string} [message='This field is required'] - The error message to display.
 * @example
 * addFieldError(emailInput, 'Please enter a valid email');
 */
export function addFieldError(inputEl, message = 'This field is required') {
  if (!inputEl) return;

  inputEl.classList.add('ring-2', 'ring-red-300', 'border-red-500');

  const errorKey = `error-for-${inputEl.id}`;
  let errorEl = document.getElementById(errorKey);

  if (!errorEl) {
    errorEl = document.createElement('p');
    errorEl.id = errorKey;
    errorEl.className = 'text-xs text-red-600 mt-1';
    inputEl.parentElement.appendChild(errorEl);
  }

  errorEl.textContent = message;
}

/**
 * Removes error styling and message from a form field.
 * @param {HTMLElement} inputEl - The input element to clear errors from.
 * @example
 * clearFieldError(emailInput);
 */
export function clearFieldError(inputEl) {
  if (!inputEl) return;

  inputEl.classList.remove('ring-2', 'ring-red-300', 'border-red-500');

  const errorKey = `error-for-${inputEl.id}`;
  const errorEl = document.getElementById(errorKey);

  if (errorEl) {
    errorEl.remove();
  }
}

/**
 * Clears all error messages and styling in a given form step.
 * @param {number} stepIndex - The index of the form step.
 * @example
 * clearAllErrorsInStep(0);
 */
export function clearAllErrorsInStep(stepIndex) {
  const formSteps = document.querySelectorAll('.form-step');
  const stepEl = formSteps[stepIndex];

  if (!stepEl) return;

  stepEl.querySelectorAll('input, select, textarea').forEach(el => clearFieldError(el));
}

/**
 * Scrolls an element into view with smooth behavior.
 * @param {HTMLElement} el - The element to scroll into view.
 * @example
 * smoothScrollIntoView(invalidField);
 */
export function smoothScrollIntoView(el) {
  if (el && typeof el.scrollIntoView === 'function') {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

/**
 * Toggles visibility of a DOM element.
 * @param {HTMLElement} el - The element to toggle.
 * @param {boolean} [show] - Optional: explicitly show (true) or hide (false).
 * @example
 * toggleVisibility(loadingSpinner, true);
 */
export function toggleVisibility(el, show) {
  if (!el) return;

  if (typeof show === 'boolean') {
    el.classList.toggle('hidden', !show);
  } else {
    el.classList.toggle('hidden');
  }
}

/**
 * Helper to set multiple visibility states at once.
 * @param {Object} states - Map of element IDs to boolean visibility states.
 * @example
 * setMultipleVisibility({
 *   'loadingSpinner': false,
 *   'resultsSection': true,
 *   'adviceContent': true
 * });
 */
export function setMultipleVisibility(states) {
  Object.entries(states).forEach(([id, show]) => {
    const el = document.getElementById(id);
    if (el) {
      toggleVisibility(el, show);
    }
  });
}

/**
 * Copies text to clipboard and shows a toast notification.
 * @param {string} text - The text to copy.
 * @param {string} [successMessage='Copied to clipboard!'] - Success message to display.
 * @example
 * copyToClipboard(adviceText, 'Advice copied!');
 */
export async function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
  try {
    await navigator.clipboard.writeText(text);
    showToast(successMessage, 'success');
    return true;
  } catch (error) {
    console.error('Clipboard copy failed:', error);
    showToast('Failed to copy to clipboard', 'error');
    return false;
  }
}

/**
 * Safely retrieves a DOM element and logs if not found.
 * @param {string} id - The element ID.
 * @param {boolean} [logError=true] - Whether to log if element is not found.
 * @returns {HTMLElement|null} The element or null.
 * @example
 * const button = safeGetElement('submitBtn');
 */
export function safeGetElement(id, logError = true) {
  const el = document.getElementById(id);
  if (!el && logError) {
    console.warn(`Element with ID "${id}" not found in DOM`);
  }
  return el;
}

export default {
  showToast,
  setButtonLoading,
  addFieldError,
  clearFieldError,
  clearAllErrorsInStep,
  smoothScrollIntoView,
  toggleVisibility,
  setMultipleVisibility,
  copyToClipboard,
  safeGetElement
};
