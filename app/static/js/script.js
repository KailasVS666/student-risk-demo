/**
 * Main Application Script
 * Orchestrates all modules and initializes the application.
 * Uses ES6 modules for clean separation of concerns.
 */

// ============================================================================
// IMPORTS
// ============================================================================

import APP_CONFIG from './config.js';
import {
  showToast,
  setButtonLoading,
  clearFieldError,
  toggleVisibility,
  setMultipleVisibility,
  copyToClipboard,
  safeGetElement
} from './ui-utils.js';

import {
  gatherFormData,
  validateStep,
  validateFieldInline,
  populateFormWithData,
  clearForm,
  markFormDirty,
  markFormClean,
  startAutoSave,
  restoreFormFromLocalStorage,
  clearAutoSavedForm
} from './form-utils.js';

import {
  initializeFirebase,
  waitForAuthState,
  saveProfile,
  loadProfile,
  loadProfileNames,
  signInUser,
  signUpUser,
  signOutUser
} from './firebase-utils.js';

import {
  predictRisk,
  generatePDF,
  downloadPDFFile
} from './api.js';

import {
  renderExplanationChart,
  renderGradesChart,
  renderProbaChart,
  filterSensitiveFeatures,
  destroyAllCharts
} from './charts.js';

import {
  WizardManager,
  initializeWizard
} from './wizard.js';

import {
  updateRiskBadge,
  renderAdvice,
  displayResults,
  clearResults
} from './results.js';

import { setupThemeToggle } from './theme.js';
import { handleError, withErrorBoundary } from './error-handler.js';
import { clearCache } from './cache.js';

// ============================================================================
// GLOBAL STATE
// ============================================================================

let wizard = null;
let firebaseServices = null;
let currentUserEmail = null;
let lastShapValuesRaw = null;
let currentAssessmentResults = null;
let stepIndicatorText = null;

function isQuotaErrorPayload(payload) {
  const text = (payload?.mentoring_advice || payload?.error || '').toString().toLowerCase();
  return text.includes('quota') || text.includes('rate limit') || text.includes('429');
}

// ============================================================================
// UI HELPERS
// ============================================================================

function setActionProgress(show, message) {
  const container = safeGetElement('actionProgress', false);
  const textEl = safeGetElement('actionProgressText', false);

  if (container) {
    container.classList.toggle('hidden', !show);
  }

  if (textEl && message) {
    textEl.textContent = message;
  }
}

function toggleResultsSkeleton(show) {
  const skeleton = safeGetElement('resultsSkeleton', false);
  if (skeleton) {
    skeleton.classList.toggle('hidden', !show);
  }
}

// Make available globally for external access if needed
window.wizard = null;
window.currentAssessmentResults = null;
window.currentUserEmail = null;

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initializes the entire application.
 * Called when DOM is ready.
 */
async function initializeApp() {
  try {
    // 1. Initialize Firebase
    firebaseServices = initializeFirebase();
    if (!firebaseServices) {
      console.error('Failed to initialize Firebase. Auth features disabled.');
      showToast('Firebase initialization failed. Some features may not work.', 'error');
    }

    // 2. Initialize Form Wizard
    wizard = initializeWizard({ totalSteps: 3 });
    window.wizard = wizard;
    if (!wizard) {
      console.error('Failed to initialize wizard');
      showToast('Form wizard failed to initialize', 'error');
    }

    // 3. Setup Theme Toggle
    setupThemeToggle();

    // 4. Setup Auto-save and Restore Form
    startAutoSave();
    const savedFormData = restoreFormFromLocalStorage();
    if (savedFormData && Object.keys(savedFormData).length > 0) {
      const restoreBtn = confirm('Would you like to restore your previous assessment?');
      if (restoreBtn) {
        populateFormWithData(savedFormData);
        showToast('Form data restored', 'success');
      } else {
        clearAutoSavedForm();
      }
    }

    // 5. Setup Form Event Listeners
    setupFormEventListeners();

    // 6. Setup Prediction & Results Event Listeners
    setupPredictionEventListeners();

    // 7. Setup Firebase Auth Event Listeners
    if (firebaseServices) {
      setupFirebaseAuthListeners();
    }

    // 8. Setup UI Event Listeners
    setupUIEventListeners();

    // 9. Setup Unsaved Changes Guard
    setupUnsavedChangesGuard();
  } catch (error) {
    handleError(error, { context: 'Application Initialization' });
  }
}

function updateActionBarStep(wizardInstance) {
  if (!wizardInstance) return;
  const labelEl = safeGetElement('actionStepLabel', false);
  const titleEl = safeGetElement('actionStepTitle', false);

  const current = wizardInstance.getCurrentStep();
  const total = wizardInstance.getTotalSteps();
  const title = wizardInstance.getStepLabel(current);

  if (labelEl) {
    labelEl.textContent = `Step ${current + 1} of ${total}`;
  }

  if (titleEl) {
    titleEl.textContent = title;
  }
}

// ============================================================================
// FORM EVENT LISTENERS
// ============================================================================

/**
 * Sets up event listeners for form fields.
 */
function setupFormEventListeners() {
  const inputForm = document.getElementById('inputForm');
  if (!inputForm) return;

  // Clear field errors on input
  inputForm.querySelectorAll('input, select, textarea').forEach(field => {
    field.addEventListener('input', () => {
      clearFieldError(field);
      markFormDirty();
    });

    field.addEventListener('change', () => {
      clearFieldError(field);
      markFormDirty();
      validateFieldInline(field);
    });

    field.addEventListener('blur', () => {
      validateFieldInline(field);
    });
  });

  // Clear Form Button
  const clearFormBtn = safeGetElement('clearFormBtn', false);
  if (clearFormBtn) {
    clearFormBtn.addEventListener('click', () => {
      clearForm();
      clearResults();
      clearAutoSavedForm();
      markFormClean();
    });
  }
}

// ============================================================================
// PREDICTION & RESULTS EVENT LISTENERS
// ============================================================================

/**
 * Sets up event listeners for prediction and result display.
 */
function setupPredictionEventListeners() {
  const generateAdviceButtons = document.querySelectorAll('#generateAdviceBtn');
  if (!generateAdviceButtons?.length) return;

  generateAdviceButtons.forEach(btn => {
    btn.addEventListener('click', async () => {
      await handlePredictionRequest(generateAdviceButtons);
    });
  });
}

/**
 * Handles the full prediction workflow.
 * @private
 */
async function handlePredictionRequest(generateAdviceButtons = []) {
  const formData = gatherFormData();

  if (!formData) {
    showToast('Failed to gather form data', 'error');
    return;
  }

  // Show loading state
  if (generateAdviceButtons?.length) {
    generateAdviceButtons.forEach(btn => setButtonLoading(btn, true, 'Generate Mentoring Advice'));
  }

  setMultipleVisibility({
    resultsSection: true,
    loadingSpinner: false,
    resultsSkeleton: true,
    adviceContent: false,
    explanationChartContainer: false
  });

  setActionProgress(true, 'Analyzing profile and generating mentoring advice...');
  toggleResultsSkeleton(true);

  try {
    // 1. Call prediction API
    const result = await predictRisk(formData);

    // 2. Handle quota/rate-limit gracefully with a friendly message
    const quotaHit = isQuotaErrorPayload(result);
    const safeAdvice = quotaHit
      ? 'We hit our AI quota just now. Please retry in about a minute, or switch to a key/project with available quota.'
      : result.mentoring_advice;

    if (quotaHit) {
      showToast('AI quota is exhausted. Try again shortly.', 'error');
    }

    // 3. Update global state
    currentAssessmentResults = {
      predicted_grade: result.prediction,
      risk_category: result.risk_category,
      confidence: result.confidence,
      mentoring_advice: safeAdvice,
      shap_values: result.shap_values
    };

    window.currentAssessmentResults = currentAssessmentResults;

    // 3. Hide loading
    setMultipleVisibility({
      loadingSpinner: false,
      resultsSkeleton: false,
      adviceContent: true,
      explanationChartContainer: true
    });
    setActionProgress(false);
    toggleResultsSkeleton(false);

    // 4. Render results (with friendly advice text if quota hit)
    displayResults({ ...result, mentoring_advice: safeAdvice });

    // 5. Render charts
    if (result.probabilities) {
      renderProbaChart(result.probabilities);
    }

    lastShapValuesRaw = result.shap_values || [];
    renderExplanationChart(lastShapValuesRaw);
    renderGradesChart(formData.G1, formData.G2, result.prediction);

    // 6. Show PDF button
    const pdfBtn = safeGetElement('downloadPdfBtn', false);
    if (pdfBtn) {
      pdfBtn.style.display = 'flex';
    }

    // 7. Persist to Firebase if auto-save is enabled
    await persistAssessmentResults(formData, { ...result, mentoring_advice: safeAdvice });

    showToast('Analysis complete!', 'success');
    markFormClean();
  } catch (error) {
    handleError(error, { context: 'Risk Prediction' });

    const quotaError = isQuotaErrorPayload({ error: error?.message });
    if (quotaError) {
      const adviceOutput = safeGetElement('adviceOutput', false);
      if (adviceOutput) {
        adviceOutput.innerHTML = '<p class="text-sm">We hit our AI quota. Please retry in about a minute, or switch to a key/project with available quota.</p>';
      }
    }

    setMultipleVisibility({
      loadingSpinner: false,
      resultsSkeleton: false,
      adviceContent: quotaError,
      explanationChartContainer: false
    });
    setActionProgress(false);
    toggleResultsSkeleton(false);
  } finally {
    if (generateAdviceButtons?.length) {
      generateAdviceButtons.forEach(btn => setButtonLoading(btn, false, 'Generate Mentoring Advice'));
    }
  }
}

/**
 * Persists assessment results to Firebase.
 * @param {Object} formData - The form data.
 * @param {Object} result - The prediction result.
 * @private
 */
async function persistAssessmentResults(formData, result) {
  if (!firebaseServices || !currentUserEmail) {
    return; // Firebase not available or user not logged in
  }

  try {
    const { db } = firebaseServices;
    const timestamp = new Date().toISOString();
    const docName = `assessment_${timestamp.replace(/[:.]/g, '-')}`;

    await saveProfile(db, currentUserEmail, docName, {
      ...formData,
      prediction: result.prediction,
      risk_category: result.risk_category,
      confidence: result.confidence,
      timestamp
    });
  } catch (error) {
    console.warn('Failed to persist assessment:', error);
    // Don't fail the entire flow if persistence fails
  }
}

// ============================================================================
// FIREBASE AUTH EVENT LISTENERS
// ============================================================================

/**
 * Sets up Firebase authentication event listeners.
 * @private
 */
function setupFirebaseAuthListeners() {
  if (!firebaseServices) return;

  const { auth, db } = firebaseServices;

  // Auth state listener
  auth.onAuthStateChanged(async user => {
    if (user) {
      // User logged in
      currentUserEmail = user.email;
      window.currentUserEmail = user.email;

      const userEmailSpan = safeGetElement('user-email', false);
      if (userEmailSpan) {
        userEmailSpan.textContent = user.email;
      }

      setMultipleVisibility({
        'auth-container': false,
        'app': true
      });

      // Load user's profiles
      await loadUserProfiles(db, user.email);
    } else {
      // User logged out
      currentUserEmail = null;
      window.currentUserEmail = null;

      const userEmailSpan = safeGetElement('user-email', false);
      if (userEmailSpan) {
        userEmailSpan.textContent = '';
      }

      setMultipleVisibility({
        'auth-container': true,
        'app': false
      });

      destroyAllCharts();
      clearResults();
    }
  });

  // Login button
  const loginBtn = safeGetElement('loginBtn', false);
  if (loginBtn) {
    loginBtn.addEventListener('click', async () => {
      await handleLogin(auth);
    });
  }

  // Signup button
  const signupBtn = safeGetElement('signupBtn', false);
  if (signupBtn) {
    signupBtn.addEventListener('click', async () => {
      await handleSignUp(auth);
    });
  }

  // Logout button
  const logoutBtn = safeGetElement('logoutBtn', false);
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      await handleLogout(auth);
    });
  }

  // Profile save button
  const saveProfileBtn = safeGetElement('saveProfileBtn', false);
  if (saveProfileBtn) {
    saveProfileBtn.addEventListener('click', async () => {
      await handleProfileSave(db);
    });
  }

  // Profile load button
  const loadProfileBtn = safeGetElement('loadProfileBtn', false);
  if (loadProfileBtn) {
    loadProfileBtn.addEventListener('click', async () => {
      await handleProfileLoad(db);
    });
  }
}

/**
 * Handles user login.
 * @param {Object} auth - Firebase auth instance.
 * @private
 */
async function handleLogin(auth) {
  const emailInput = safeGetElement('email', false);
  const passwordInput = safeGetElement('password', false);
  const authError = safeGetElement('auth-error', false);

  if (!emailInput || !passwordInput) return;

  const email = emailInput.value.trim();
  const password = passwordInput.value;

  if (!email || !password) {
    if (authError) authError.textContent = 'Please enter email and password';
    return;
  }

  if (authError) authError.textContent = '';

  try {
    await signInUser(auth, email, password);
    showToast(APP_CONFIG.MESSAGES.LOGGED_IN, 'success');
  } catch (error) {
    const message = error.message || 'Login failed';
    if (authError) authError.textContent = message;
    showToast(message, 'error');
  }
}

/**
 * Handles user signup.
 * @param {Object} auth - Firebase auth instance.
 * @private
 */
async function handleSignUp(auth) {
  const emailInput = safeGetElement('email', false);
  const passwordInput = safeGetElement('password', false);
  const authError = safeGetElement('auth-error', false);

  if (!emailInput || !passwordInput) return;

  const email = emailInput.value.trim();
  const password = passwordInput.value;

  if (!email || !password) {
    if (authError) authError.textContent = 'Please enter email and password';
    return;
  }

  if (authError) authError.textContent = '';

  try {
    await signUpUser(auth, email, password);
    showToast(APP_CONFIG.MESSAGES.SIGNED_UP, 'success');
  } catch (error) {
    const message = error.message || 'Signup failed';
    if (authError) authError.textContent = message;
    showToast(message, 'error');
  }
}

/**
 * Handles user logout.
 * @param {Object} auth - Firebase auth instance.
 * @private
 */
async function handleLogout(auth) {
  try {
    await signOutUser(auth);
    showToast(APP_CONFIG.MESSAGES.LOGGED_OUT, 'info');
  } catch (error) {
    console.error('Logout error:', error);
    showToast(APP_CONFIG.MESSAGES.LOGOUT_ERROR, 'error');
  }
}

/**
 * Handles profile save.
 * @param {Object} db - Firestore database instance.
 * @private
 */
async function handleProfileSave(db) {
  const saveBtn = safeGetElement('saveProfileBtn', false);
  const profileNameInput = safeGetElement('profileName', false);

  if (!currentUserEmail) {
    showToast(APP_CONFIG.MESSAGES.NO_AUTH, 'error');
    return;
  }

  if (!profileNameInput) return;

  const profileName = profileNameInput.value.trim();
  if (!profileName) {
    showToast(APP_CONFIG.MESSAGES.PROFILE_NAME_REQUIRED, 'error');
    return;
  }

  const profileData = gatherFormData();
  if (!profileData) {
    showToast('Failed to gather form data', 'error');
    return;
  }

  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.dataset.originalText = saveBtn.innerText;
    saveBtn.innerText = APP_CONFIG.BUTTON_TEXT.SAVING;
  }

  try {
    await saveProfile(db, currentUserEmail, profileName, profileData);
    showToast(APP_CONFIG.MESSAGES.PROFILE_SAVED(profileName), 'success');
    await loadUserProfiles(db, currentUserEmail);
    markFormClean();
  } catch (error) {
    console.error('Error saving profile:', error);
    showToast(APP_CONFIG.MESSAGES.SAVE_ERROR, 'error');
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerText = saveBtn.dataset.originalText || APP_CONFIG.BUTTON_TEXT.SAVE_PROFILE;
    }
  }
}

/**
 * Handles profile load.
 * @param {Object} db - Firestore database instance.
 * @private
 */
async function handleProfileLoad(db) {
  const loadBtn = safeGetElement('loadProfileBtn', false);
  const selectElement = safeGetElement('loadProfileSelect', false);

  if (!selectElement) return;

  const profileName = selectElement.value;
  if (!profileName) {
    showToast(APP_CONFIG.MESSAGES.NO_PROFILE_SELECTED, 'info');
    return;
  }

  if (!currentUserEmail) {
    showToast(APP_CONFIG.MESSAGES.NO_AUTH, 'error');
    return;
  }

  if (loadBtn) {
    loadBtn.disabled = true;
    loadBtn.dataset.originalText = loadBtn.innerText;
    loadBtn.innerText = APP_CONFIG.BUTTON_TEXT.LOADING;
  }

  try {
    const profileData = await loadProfile(db, currentUserEmail, profileName);
    populateFormWithData(profileData);
    showToast(APP_CONFIG.MESSAGES.PROFILE_LOADED(profileName), 'success');
    safeGetElement('profileName', false).value = profileName;
    markFormClean();
  } catch (error) {
    console.error('Error loading profile:', error);
    showToast(APP_CONFIG.MESSAGES.LOAD_ERROR, 'error');
  } finally {
    if (loadBtn) {
      loadBtn.disabled = false;
      loadBtn.innerText = loadBtn.dataset.originalText || APP_CONFIG.BUTTON_TEXT.LOAD_PROFILE;
    }
  }
}

/**
 * Loads user's saved profiles into dropdown.
 * @param {Object} db - Firestore database instance.
 * @param {string} userEmail - User's email.
 * @private
 */
async function loadUserProfiles(db, userEmail) {
  const selectElement = safeGetElement('loadProfileSelect', false);
  if (!selectElement) return;

  selectElement.innerHTML = '<option value="">- Select a profile -</option>';

  try {
    const profileNames = await loadProfileNames(db, userEmail);
    profileNames.forEach(name => {
      const option = document.createElement('option');
      option.value = name;
      option.textContent = name;
      selectElement.appendChild(option);
    });

    if (profileNames.length > 0) {
      showToast(APP_CONFIG.MESSAGES.PROFILES_LOADED, 'info');
    }
  } catch (error) {
    console.error('Error loading profiles:', error);
    showToast(APP_CONFIG.MESSAGES.PROFILES_LOAD_ERROR, 'error');
  }
}

// ============================================================================
// UI EVENT LISTENERS
// ============================================================================

/**
 * Sets up UI-specific event listeners.
 */
function setupUIEventListeners() {
  // Sensitive feature toggle
  const toggleSensitive = safeGetElement('toggleSensitive', false);
  if (toggleSensitive) {
    toggleSensitive.addEventListener('change', () => {
      if (lastShapValuesRaw) {
        const showSensitive = toggleSensitive.checked;
        renderExplanationChart(lastShapValuesRaw, showSensitive);
      }
    });
  }

  // Copy advice button
  const copyAdviceBtn = safeGetElement('copyAdviceBtn', false);
  if (copyAdviceBtn) {
    copyAdviceBtn.addEventListener('click', async () => {
      const adviceOutput = safeGetElement('adviceOutput', false);
      if (adviceOutput) {
        await copyToClipboard(adviceOutput.innerText, 'Advice copied to clipboard!');
      }
    });
  }

  // Download PDF button
  const downloadPdfBtn = safeGetElement('downloadPdfBtn', false);
  if (downloadPdfBtn) {
    downloadPdfBtn.addEventListener('click', async () => {
      await handlePDFDownload();
    });
  }
}

/**
 * Handles PDF download workflow.
 * @private
 */
async function handlePDFDownload() {
  const downloadPdfBtn = safeGetElement('downloadPdfBtn', false);

  if (!currentAssessmentResults) {
    showToast(APP_CONFIG.MESSAGES.NO_ASSESSMENT_RESULTS, 'error');
    return;
  }

  if (downloadPdfBtn) {
    downloadPdfBtn.disabled = true;
    downloadPdfBtn.textContent = APP_CONFIG.BUTTON_TEXT.PDF_GENERATING;
  }

  setActionProgress(true, 'Generating PDF report...');

  try {
    const pdfBlob = await generatePDF(currentAssessmentResults);
    downloadPDFFile(pdfBlob, `student_report_${Date.now()}.pdf`);
    showToast(APP_CONFIG.MESSAGES.PDF_SUCCESS, 'success');
  } catch (error) {
    console.error('PDF download error:', error);
    showToast(APP_CONFIG.MESSAGES.PDF_ERROR, 'error');
  } finally {
    setActionProgress(false);

    if (downloadPdfBtn) {
      downloadPdfBtn.disabled = false;
      downloadPdfBtn.innerHTML = `
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
        </svg>
        Download PDF Report
      `;
    }
  }
}

// ============================================================================
// UNSAVED CHANGES GUARD
// ============================================================================

/**
 * Sets up warning for unsaved changes.
 * @private
 */
function setupUnsavedChangesGuard() {
  const inputForm = document.getElementById('inputForm');
  if (!inputForm) return;

  window.__formDirty = false;

  // Track form changes
  inputForm.addEventListener('input', () => {
    markFormDirty();
  });

  // Warn before unload
  window.addEventListener('beforeunload', (e) => {
    if (window.__formDirty) {
      e.preventDefault();
      e.returnValue = '';
    }
  });

  // Clear dirty flag on successful submission
  const generateAdviceBtn = safeGetElement('generateAdviceBtn', false);
  if (generateAdviceBtn) {
    generateAdviceBtn.addEventListener('click', () => {
      markFormClean();
    });
  }
}

// ============================================================================
// APP STARTUP
// ============================================================================

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  initializeApp();
});

// Export for debugging/testing
export {
  initializeApp,
  handlePredictionRequest,
  handleLogin,
  handleSignUp,
  handleLogout
};
