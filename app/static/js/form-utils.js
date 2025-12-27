/**
 * Form Utilities & Helpers
 * Handles form data gathering, validation, and manipulation.
 */

import APP_CONFIG from './config.js';
import { addFieldError, clearFieldError, clearAllErrorsInStep, smoothScrollIntoView, showToast } from './ui-utils.js';

// Auto-save timer
let autoSaveTimer = null;
let formDirtyFlag = false;

/**
 * Sanitizes text input to prevent XSS attacks.
 * Removes HTML tags and dangerous characters.
 * 
 * @param {string} text - Text to sanitize
 * @returns {string} Sanitized text
 */
export function sanitizeInput(text) {
    if (typeof text !== 'string') return text;
    
    // Remove HTML tags using DOM API (safer than regex)
    const div = document.createElement('div');
    div.textContent = text;
    let sanitized = div.innerHTML;
    
    // Remove dangerous patterns
    sanitized = sanitized
        .replace(/[<>]/g, '') // Remove angle brackets
        .replace(/javascript:/gi, '') // Remove javascript: protocol
        .replace(/on\w+=/gi, ''); // Remove event handlers
    
    return sanitized;
}

/**
 * Saves form data to localStorage for auto-recovery.
 * @private
 */
export function saveFormToLocalStorage() {
  try {
    const formData = gatherFormData();
    if (formData && Object.keys(formData).length > 0) {
      localStorage.setItem(APP_CONFIG.AUTOSAVE_KEY, JSON.stringify({
        data: formData,
        timestamp: Date.now()
      }));
    }
  } catch (error) {
    console.error('Failed to auto-save form:', error);
  }
}

/**
 * Restores form data from localStorage.
 * @returns {Object|null} Saved form data or null
 */
export function restoreFormFromLocalStorage() {
  try {
    const saved = localStorage.getItem(APP_CONFIG.AUTOSAVE_KEY);
    if (saved) {
      const { data, timestamp } = JSON.parse(saved);
      // Only restore if saved within last 24 hours
      if (Date.now() - timestamp < 24 * 60 * 60 * 1000) {
        return data;
      }
    }
  } catch (error) {
    console.error('Failed to restore form:', error);
  }
  return null;
}

/**
 * Clears auto-saved form data from localStorage.
 */
export function clearAutoSavedForm() {
  try {
    localStorage.removeItem(APP_CONFIG.AUTOSAVE_KEY);
  } catch (error) {
    console.error('Failed to clear auto-saved form:', error);
  }
}

/**
 * Starts auto-save timer for form data.
 */
export function startAutoSave() {
  if (autoSaveTimer) {
    clearInterval(autoSaveTimer);
  }
  autoSaveTimer = setInterval(() => {
    if (formDirtyFlag) {
      saveFormToLocalStorage();
      formDirtyFlag = false;
    }
  }, APP_CONFIG.AUTOSAVE_INTERVAL);
}

/**
 * Gathers all form data from input fields into a single object.
 * Sanitizes text inputs to prevent XSS.
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
      formData[input.id] = sanitizeInput(String(value).trim());
    } else if (input.tagName === 'TEXTAREA') {
      formData[input.id] = sanitizeInput(String(value).trim());
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

function getValidationResult(el) {
  const valueRaw = (el.value ?? '').toString().trim();

  if (!valueRaw && valueRaw !== '0') {
    return { valid: false, message: APP_CONFIG.MESSAGES.REQUIRED_FIELD };
  }

  const id = el.id;
  const v = Number(valueRaw);
  const isNumeric = ['range', 'number'].includes(el.type);

  const within = (num, min, max) => num >= min && num <= max;

  if (isNumeric) {
    if (Number.isNaN(v)) {
      return { valid: false, message: 'Enter a numeric value.' };
    }

    switch (id) {
      case 'age':
        if (!within(v, APP_CONFIG.VALIDATION.MIN_AGE, APP_CONFIG.VALIDATION.MAX_AGE)) {
          return { valid: false, message: `Age must be ${APP_CONFIG.VALIDATION.MIN_AGE}-${APP_CONFIG.VALIDATION.MAX_AGE}.` };
        }
        break;
      case 'studytime':
        if (!within(v, APP_CONFIG.VALIDATION.MIN_STUDY_TIME, APP_CONFIG.VALIDATION.MAX_STUDY_TIME)) {
          return { valid: false, message: `Study time must be ${APP_CONFIG.VALIDATION.MIN_STUDY_TIME}-${APP_CONFIG.VALIDATION.MAX_STUDY_TIME}.` };
        }
        break;
      case 'traveltime':
        if (!within(v, APP_CONFIG.VALIDATION.MIN_TRAVELTIME, APP_CONFIG.VALIDATION.MAX_TRAVELTIME)) {
          return { valid: false, message: 'Travel time must be 1-4.' };
        }
        break;
      case 'freetime':
        if (!within(v, APP_CONFIG.VALIDATION.MIN_FREETIME, APP_CONFIG.VALIDATION.MAX_FREETIME)) {
          return { valid: false, message: 'Free time must be 1-5.' };
        }
        break;
      case 'goout':
        if (!within(v, APP_CONFIG.VALIDATION.MIN_GOOUT, APP_CONFIG.VALIDATION.MAX_GOOUT)) {
          return { valid: false, message: 'Going out must be 1-5.' };
        }
        break;
      case 'Dalc':
      case 'Walc':
        if (!within(v, APP_CONFIG.VALIDATION.MIN_ALC, APP_CONFIG.VALIDATION.MAX_ALC)) {
          return { valid: false, message: 'Alcohol use must be 1-5.' };
        }
        break;
      case 'health':
        if (!within(v, APP_CONFIG.VALIDATION.MIN_HEALTH, APP_CONFIG.VALIDATION.MAX_HEALTH)) {
          return { valid: false, message: 'Health must be 1-5.' };
        }
        break;
      case 'failures':
        if (!within(v, APP_CONFIG.VALIDATION.MIN_FAILURES, APP_CONFIG.VALIDATION.MAX_FAILURES)) {
          return { valid: false, message: 'Failures must be 0-4.' };
        }
        break;
      case 'absences':
        if (!within(v, APP_CONFIG.VALIDATION.MIN_ABSENCES, APP_CONFIG.VALIDATION.MAX_ABSENCES)) {
          return { valid: false, message: 'Absences must be 0-93.' };
        }
        break;
      case 'G1':
      case 'G2':
        if (!within(v, APP_CONFIG.VALIDATION.MIN_GRADE, APP_CONFIG.VALIDATION.MAX_GRADE)) {
          return { valid: false, message: 'Grades must be 0-20.' };
        }
        break;
      default:
        break;
    }
  }

  return { valid: true };
}

export function validateFieldInline(el) {
  if (!el) return true;

  const { valid, message } = getValidationResult(el);

  if (!valid) {
    addFieldError(el, message);
  } else {
    clearFieldError(el);
  }

  return valid;
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

    const { valid, message } = getValidationResult(el);

    if (!valid) {
      addFieldError(el, message);
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
  formDirtyFlag = true; // Also mark for auto-save
}

/**
 * Marks the form as saved (no unsaved changes).
 * @example
 * markFormClean();
 */
export function markFormClean() {
  window.__formDirty = false;
  formDirtyFlag = false; // Also clear auto-save flag
}

/**
 * Checks if form has unsaved changes.
 * @returns {boolean} True if form has unsaved changes.
 * @example
 * if (isFormDirty()) { ... }
 */
export function isFormDirty() {
  return window.__formDirty || formDirtyFlag || false;
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
  validateFieldInline,
  populateFormWithData,
  clearForm,
  markFormDirty,
  markFormClean,
  isFormDirty,
  getFormFieldValue,
  setFormFieldValue,
  validateAllSteps
};
