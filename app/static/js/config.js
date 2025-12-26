/**
 * Shared Configuration & Constants
 * Central place for API endpoints, UI strings, validation rules, and other constants.
 * Makes it easy to maintain and update configuration across the app.
 */

const APP_CONFIG = {
  // ===== API Endpoints =====
  API: {
    PREDICT: '/api/predict',
    GENERATE_PDF: '/generate-pdf',
    HEALTHZ: '/healthz',
    STATUS: '/status'
  },

  // ===== Form Step Configuration =====
  FORM_STEPS: {
    DEMOGRAPHICS: 0,
    FAMILY_EDUCATION: 1,
    ACADEMIC_SOCIAL: 2
  },

  // ===== Required Fields by Form Step =====
  REQUIRED_FIELDS_BY_STEP: {
    0: ['school', 'sex', 'age', 'address', 'famsize', 'Pstatus', 'famrel'],
    1: ['Medu', 'Fedu', 'Mjob', 'Fjob', 'studytime', 'reason', 'guardian', 'schoolsup', 'famsup', 'paid', 'higher'],
    2: ['activities', 'nursery', 'internet', 'romantic', 'traveltime', 'freetime', 'goout', 'Dalc', 'Walc', 'health', 'absences', 'failures', 'G1', 'G2']
  },

  // ===== Risk Categories & Colors =====
  RISK_LEVELS: {
    HIGH: 'high',
    MEDIUM: 'medium',
    LOW: 'low'
  },

  RISK_COLORS: {
    high: '#EF4444',      // Red
    medium: '#F59E0B',    // Amber
    low: '#10B981'        // Green
  },

  // ===== Grade Ranges by Risk Category =====
  GRADE_RANGES: {
    0: { min: 0, max: 9, label: 'High Risk' },
    1: { min: 14, max: 20, label: 'Low Risk' },
    2: { min: 10, max: 13, label: 'Medium Risk' }
  },

  // ===== Toast Notification Types =====
  TOAST_TYPES: {
    SUCCESS: 'success',
    ERROR: 'error',
    INFO: 'info'
  },

  // ===== Sensitive Feature Keywords (for privacy filtering) =====
  SENSITIVE_KEYWORDS: ['sex', 'gender', 'age', 'guardian', 'address', 'famsize', 'pstatus', 'mjob', 'fjob', 'romantic'],

  // ===== Chart Configuration =====
  CHARTS: {
    EXPLANATION_POSITIVE_COLOR: '#10B981',  // Green
    EXPLANATION_NEGATIVE_COLOR: '#EF4444',  // Red
    GRADES_LINE_COLOR: '#4F46E5',           // Indigo
    GRADES_FILL_COLOR: 'rgba(79, 70, 229, 0.1)',
    GRADE_MAX: 20,
    CHART_FONT_SIZE: 12,
    CHART_TENSION: 0.3
  },

  // ===== UI Text & Strings =====
  MESSAGES: {
    FORM_INCOMPLETE: 'Please complete the highlighted fields before continuing.',
    INVALID_GRADES: 'Grades must be zero or positive.',
    PROFILE_SAVED: (name) => `Profile "${name}" saved successfully!`,
    PROFILE_LOADED: (name) => `Profile "${name}" loaded!`,
    PROFILE_NOT_FOUND: (name) => `Profile "${name}" not found.`,
    LOGGED_IN: 'Logged in successfully!',
    SIGNED_UP: 'Account created! You are now logged in.',
    LOGGED_OUT: 'Logged out successfully.',
    NO_PROFILE_SELECTED: 'Please select a profile to load.',
    NO_AUTH: 'You must be logged in to save a profile.',
    FORM_CLEARED: 'Form cleared.',
    ADVICE_COPIED: 'Advice copied to clipboard!',
    NO_ASSESSMENT_RESULTS: 'No assessment results available. Please run an analysis first.',
    PDF_GENERATING: 'Generating...',
    PDF_SUCCESS: 'PDF downloaded successfully!',
    PDF_ERROR: 'Error generating PDF',
    ANALYSIS_COMPLETE: 'Analysis complete!',
    PROFILES_LOADED: 'Saved profiles loaded.',
    PROFILES_LOAD_ERROR: 'Could not load profiles (check permissions).',
    FIREBASE_CONFIG_MISSING: 'Firebase config missing.',
    FIREBASE_PROJECT_ID_MISSING: 'Firebase project ID missing. Save/Load disabled.',
    FIREBASE_INITIALIZATION_ERROR: 'Error initializing Firebase config.',
    FIREBASE_SDK_MISSING: 'Firebase SDK or FIREBASE_CONFIG is missing. App cannot start.',
    LOGOUT_ERROR: 'Error logging out.',
    PROFILE_NAME_REQUIRED: 'Please enter a name for the profile.',
    SAVE_ERROR: 'Error saving profile.',
    LOAD_ERROR: 'Error loading profile.',
    PERMISSION_ERROR: 'Error loading profiles.',
    PROFILE_NOT_FOUND_ERROR: 'Profile not found.',
    INVALID_INPUT: 'Invalid input provided.',
    SERVER_ERROR: 'Server error. Please try again.',
    NETWORK_ERROR: 'Network error. Please check your connection.'
  },

  // ===== Button Text =====
  BUTTON_TEXT: {
    SUBMIT: 'Submit',
    LOADING: 'Loading...',
    ANALYZING: 'Analyzing...',
    SAVE_PROFILE: 'Save Profile',
    LOAD_PROFILE: 'Load Profile',
    SAVING: 'Saving...',
    CLEAR_FORM: 'Clear Form',
    COPY_ADVICE: 'Copy Advice',
    DOWNLOAD_PDF: 'Download PDF Report',
    LOGOUT: 'Logout',
    LOGIN: 'Login',
    SIGNUP: 'Sign Up'
  },

  // ===== Validation Rules =====
  VALIDATION: {
    MIN_GRADE: 0,
    MAX_GRADE: 20,
    MIN_STUDY_TIME: 1,
    MAX_STUDY_TIME: 4,
    MIN_AGE: 15,
    MAX_AGE: 25
  },

  // ===== Probability Labels Order =====
  PROBABILITY_LABELS_ORDER: ['High', 'Medium', 'Low'],

  // ===== Feature Readable Names =====
  READABLE_FEATURE_NAMES: {
    'G1': 'First Grade',
    'G2': 'Second Grade',
    'failures': 'Past Failures',
    'studytime': 'Weekly Study Time',
    'absences': 'Absences',
    'Medu': "Mother's Education",
    'Fedu': "Father's Education",
    'goout': 'Going Out',
    'health': 'Health Status',
    'famrel': 'Family Relations'
  }
};

export default APP_CONFIG;
