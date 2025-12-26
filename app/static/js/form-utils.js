/**
 * Form Utilities & Helpers
 * Handles form data gathering, validation, and manipulation.
 */

import APP_CONFIG from './config.js';
import { addFieldError, clearFieldError, clearAllErrorsInStep, smoothScrollIntoView, showToast } from './ui-utils.js';

/**
 * Gathers all form data from input fields into a single object.
 * @returns {Object|null} Form data object or null if invalid.
 * @example
 * const formData = gatherFormData();
 */
export function gatherFormData() {
  const formData = {};

  // Get all form inputs
  const inputs = document.querySelectorAll('#inputForm input, #inputForm select, #inputForm textarea');

  inputs.forEach(input => {
    const value = input.value;

    if (!value && value !== '0') {
      console.warn(`Empty value for field: ${input.id}`);
      return;
    }

    // Convert range/number inputs to numbers
    if (input.type === 'range' || input.type === 'number') {
      formData[input.id] = Number(value);
    } else if (input.tagName === 'SELECT' || input.type === 'text') {
      formData[input.id] = String(value).trim();
    } else if (input.tagName === 'TEXTAREA') {
      formData[input.id] = String(value).trim();
    } else {
      formData[input.id] = value;
    }
  });

  // Calculate derived fields
  const g1 = formData.G1 || 0;
  const g2 = formData.G2 || 0;

  formData.average_grade = (g1 + g2) / 2;
  formData.grade_change = g2 - g1;

  return Object.keys(formData).length > 0 ? formData : null;
}

/**
 * Validates a specific form step.
 * @param {number} step - The step index to validate.
 * @returns {boolean} True if step is valid, false otherwise.
 * @example
 * if (!validateStep(0)) return; // Step 0 is invalid
 */
export function validateStep(step) {
  const requiredIds = APP_CONFIG.REQUIRED_FIELDS_BY_STEP[step] || [];

  clearAllErrorsInStep(step);

  let firstInvalidEl = null;

  requiredIds.forEach(id => {
    const el = document.getElementById(id);
    if (!el) {
      console.warn(`Field element not found: ${id}`);
      return;
    }

    let isValid = false;

    // Validate based on input type
    if (el.tagName === 'SELECT' || el.type === 'text' || el.tagName === 'TEXTAREA') {
      isValid = (el.value || '').toString().trim().length > 0;
    } else if (el.type === 'range' || el.type === 'number') {
      isValid = (el.value || '') !== '' && !Number.isNaN(Number(el.value));
    } else {
      isValid = (el.value || '') !== '';
    }

    if (!isValid) {
      addFieldError(el, 'Please provide a value');
      if (!firstInvalidEl) {
        firstInvalidEl = el;
      }
    }
  });

  // Special validation for grades in step 2
  if (step === 2) {
    const g1 = Number(document.getElementById('G1')?.value ?? 0);
    const g2 = Number(document.getElementById('G2')?.value ?? 0);

    if (g1 < APP_CONFIG.VALIDATION.MIN_GRADE || g2 < APP_CONFIG.VALIDATION.MIN_GRADE) {
      addFieldError(document.getElementById('G1'), 'Must be >= 0');
      addFieldError(document.getElementById('G2'), 'Must be >= 0');
      showToast(APP_CONFIG.MESSAGES.INVALID_GRADES, 'error');
      return false;
    }
  }

  if (firstInvalidEl) {
    smoothScrollIntoView(firstInvalidEl);
    showToast(APP_CONFIG.MESSAGES.FORM_INCOMPLETE, 'error');
    return false;
  }

  return true;
}

/**
 * Populates form fields with profile data.
 * @param {Object} data - The profile data object.
 * @example
 * populateFormWithData(profileData);
 */
export function populateFormWithData(data) {
  if (!data || typeof data !== 'object') {
    console.error('Invalid profile data');
    return;
  }

  Object.entries(data).forEach(([key, value]) => {
    const input = document.getElementById(key);

    if (!input) return;

    if (input.tagName === 'SELECT') {
      input.value = value || '';
    } else if (input.type === 'range') {
      input.value = value || input.getAttribute('value') || '0';
      const valueSpan = document.getElementById(`${key}Value`);
      if (valueSpan) {
        valueSpan.textContent = input.value;
      }
    } else if (input.tagName === 'TEXTAREA' || key === 'customPrompt') {
      input.value = value || '';
    } else {
      input.value = value || '';
    }
  });
}

/**
 * Clears all form inputs to their default values.
 * @example
 * clearForm();
 */
export function clearForm() {
  // Clear all select elements
  document.querySelectorAll('#inputForm select').forEach(select => {
    select.selectedIndex = 0;
  });

  // Clear and reset all range inputs
  document.querySelectorAll('#inputForm input[type="range"]').forEach(range => {
    const defaultValue = range.getAttribute('value') || '0';
    range.value = defaultValue;
    const valueSpan = document.getElementById(`${range.id}Value`);
    if (valueSpan) {
      valueSpan.textContent = defaultValue;
    }
  });

  // Clear textarea
  const customPrompt = document.getElementById('customPrompt');
  if (customPrompt) {
    customPrompt.value = '';
  }

  // Clear profile name
  const profileName = document.getElementById('profileName');
  if (profileName) {
    profileName.value = 'new_student';
  }

  showToast(APP_CONFIG.MESSAGES.FORM_CLEARED, 'info');
}

/**
 * Marks the form as having unsaved changes.
 * @example
 * markFormDirty();
 */
export function markFormDirty() {
  window.__formDirty = true;
}

/**
 * Marks the form as saved (no unsaved changes).
 * @example
 * markFormClean();
 */
export function markFormClean() {
  window.__formDirty = false;
}

/**
 * Checks if form has unsaved changes.
 * @returns {boolean} True if form has unsaved changes.
 * @example
 * if (isFormDirty()) { ... }
 */
export function isFormDirty() {
  return window.__formDirty || false;
}

/**
 * Gets a specific form field value.
 * @param {string} fieldId - The field ID.
 * @returns {*} The field value.
 * @example
 * const schoolValue = getFormFieldValue('school');
 */
export function getFormFieldValue(fieldId) {
  const field = document.getElementById(fieldId);
  if (!field) return null;

  if (field.type === 'range' || field.type === 'number') {
    return Number(field.value);
  }

  return field.value;
}

/**
 * Sets a specific form field value.
 * @param {string} fieldId - The field ID.
 * @param {*} value - The value to set.
 * @example
 * setFormFieldValue('school', 'GP');
 */
export function setFormFieldValue(fieldId, value) {
  const field = document.getElementById(fieldId);
  if (!field) return;

  field.value = value;

  // Update range display if applicable
  if (field.type === 'range') {
    const valueSpan = document.getElementById(`${fieldId}Value`);
    if (valueSpan) {
      valueSpan.textContent = value;
    }
  }

  markFormDirty();
}

/**
 * Validates all form data at once (all steps).
 * @returns {boolean} True if all steps are valid.
 * @example
 * if (!validateAllSteps()) { ... }
 */
export function validateAllSteps() {
  const totalSteps = Object.keys(APP_CONFIG.REQUIRED_FIELDS_BY_STEP).length;

  for (let step = 0; step < totalSteps; step++) {
    if (!validateStep(step)) {
      return false;
    }
  }

  return true;
}

export default {
  gatherFormData,
  validateStep,
  populateFormWithData,
  clearForm,
  markFormDirty,
  markFormClean,
  isFormDirty,
  getFormFieldValue,
  setFormFieldValue,
  validateAllSteps
};
