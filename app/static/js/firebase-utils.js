/**
 * Firebase Configuration & Initialization
 * Centralizes all Firebase setup and configuration logic.
 */

import { showToast } from './ui-utils.js';
import APP_CONFIG from './config.js';

/**
 * Initializes Firebase and returns db and auth instances.
 * @returns {Object|null} Object with {db, auth} or null if initialization failed.
 * @example
 * const firebase = initializeFirebase();
 * if (firebase) {
 *   const { db, auth } = firebase;
 * }
 */
export function initializeFirebase() {
  // Validate Firebase SDK availability
  if (typeof firebase === 'undefined') {
    console.error('Firebase SDK not loaded. Ensure <script src="https://www.gstatic.com/firebasejs/..."></script> is included.');
    showToast(APP_CONFIG.MESSAGES.FIREBASE_SDK_MISSING, 'error');
    return null;
  }

  // Validate Firebase config availability
  if (typeof window.FIREBASE_CONFIG === 'undefined') {
    console.error('FIREBASE_CONFIG not found. Check that Flask is passing config to template.');
    showToast(APP_CONFIG.MESSAGES.FIREBASE_CONFIG_MISSING, 'error');
    return null;
  }

  // Parse config if it's a string
  let config = window.FIREBASE_CONFIG;
  if (typeof config === 'string') {
    try {
      config = JSON.parse(config);
    } catch (error) {
      console.error('Failed to parse FIREBASE_CONFIG:', error);
      showToast(APP_CONFIG.MESSAGES.FIREBASE_INITIALIZATION_ERROR, 'error');
      return null;
    }
  }

  // Validate essential config properties
  if (!config || !config.projectId) {
    console.error('Firebase config missing required field: projectId');
    showToast(APP_CONFIG.MESSAGES.FIREBASE_PROJECT_ID_MISSING, 'error');
    return null;
  }

  try {
    // Initialize Firebase only if not already initialized
    if (!firebase.apps.length) {
      // Use the modern Firebase SDK initialization (avoid deprecation warning)
      // The config object should be passed directly to initializeApp
      firebase.initializeApp(config);
      console.log('Firebase initialized successfully');
    }

    const db = firebase.firestore();
    const auth = firebase.auth();

    return { db, auth };
  } catch (error) {
    console.error('Firebase initialization error:', error);
    showToast('Firebase initialization failed: ' + error.message, 'error');
    return null;
  }
}

/**
 * Sets up an onAuthStateChanged listener and returns a promise.
 * @param {Object} auth - Firebase auth instance.
 * @returns {Promise<Object>} Resolves with user object or null.
 * @example
 * const user = await waitForAuthState(auth);
 */
export async function waitForAuthState(auth) {
  return new Promise((resolve) => {
    const unsubscribe = auth.onAuthStateChanged((user) => {
      unsubscribe(); // Unsubscribe after first check
      resolve(user);
    });
  });
}

/**
 * Saves a user's profile to Firestore.
 * @param {Object} db - Firestore database instance.
 * @param {string} userEmail - The user's email.
 * @param {string} profileName - The profile name.
 * @param {Object} profileData - The profile data object.
 * @returns {Promise<boolean>} True if save was successful.
 * @example
 * await saveProfile(db, 'user@example.com', 'student_01', { G1: 8, G2: 9, ... });
 */
export async function saveProfile(db, userEmail, profileName, profileData) {
  if (!userEmail) {
    throw new Error('User email is required');
  }

  if (!profileName || profileName.trim() === '') {
    throw new Error(APP_CONFIG.MESSAGES.PROFILE_NAME_REQUIRED);
  }

  try {
    const docRef = db
      .collection('profiles')
      .doc(userEmail)
      .collection('student_data')
      .doc(profileName);

    const existing = await docRef.get();

    if (existing.exists) {
      // Update existing profile
      await docRef.set({
        ...profileData,
        updatedAt: firebase.firestore.FieldValue.serverTimestamp()
      }, { merge: true });
    } else {
      // Create new profile
      await docRef.set({
        ...profileData,
        createdAt: firebase.firestore.FieldValue.serverTimestamp(),
        updatedAt: firebase.firestore.FieldValue.serverTimestamp()
      }, { merge: true });
    }

    return true;
  } catch (error) {
    console.error('Error saving profile:', error);
    throw error;
  }
}

/**
 * Loads a specific profile from Firestore.
 * @param {Object} db - Firestore database instance.
 * @param {string} userEmail - The user's email.
 * @param {string} profileName - The profile name.
 * @returns {Promise<Object>} The profile data.
 * @example
 * const profile = await loadProfile(db, 'user@example.com', 'student_01');
 */
export async function loadProfile(db, userEmail, profileName) {
  if (!userEmail) {
    throw new Error('User email is required');
  }

  try {
    const doc = await db
      .collection('profiles')
      .doc(userEmail)
      .collection('student_data')
      .doc(profileName)
      .get();

    if (!doc.exists) {
      throw new Error(APP_CONFIG.MESSAGES.PROFILE_NOT_FOUND(profileName));
    }

    return doc.data();
  } catch (error) {
    console.error('Error loading profile:', error);
    throw error;
  }
}

/**
 * Loads all profile names for a user.
 * @param {Object} db - Firestore database instance.
 * @param {string} userEmail - The user's email.
 * @returns {Promise<Array<string>>} Array of profile names.
 * @example
 * const profiles = await loadProfileNames(db, 'user@example.com');
 */
export async function loadProfileNames(db, userEmail) {
  if (!userEmail) {
    return [];
  }

  try {
    const snapshot = await db
      .collection('profiles')
      .doc(userEmail)
      .collection('student_data')
      .get();

    if (snapshot.empty) {
      console.log('No saved profiles found');
      return [];
    }

    return snapshot.docs.map(doc => doc.id);
  } catch (error) {
    console.error('Error loading profile names:', error);
    throw error;
  }
}

/**
 * Deletes a profile from Firestore.
 * @param {Object} db - Firestore database instance.
 * @param {string} userEmail - The user's email.
 * @param {string} profileName - The profile name.
 * @returns {Promise<boolean>} True if deletion was successful.
 * @example
 * await deleteProfile(db, 'user@example.com', 'student_01');
 */
export async function deleteProfile(db, userEmail, profileName) {
  if (!userEmail) {
    throw new Error('User email is required');
  }

  try {
    await db
      .collection('profiles')
      .doc(userEmail)
      .collection('student_data')
      .doc(profileName)
      .delete();

    return true;
  } catch (error) {
    console.error('Error deleting profile:', error);
    throw error;
  }
}

/**
 * Signs in a user with email and password.
 * @param {Object} auth - Firebase auth instance.
 * @param {string} email - User email.
 * @param {string} password - User password.
 * @returns {Promise<Object>} User credential.
 * @example
 * const cred = await signInUser(auth, 'user@example.com', 'password123');
 */
export async function signInUser(auth, email, password) {
  if (!email || !password) {
    throw new Error('Email and password are required');
  }

  try {
    const userCredential = await auth.signInWithEmailAndPassword(email, password);
    return userCredential;
  } catch (error) {
    console.error('Sign-in error:', error);
    throw error;
  }
}

/**
 * Signs up a new user with email and password.
 * @param {Object} auth - Firebase auth instance.
 * @param {string} email - User email.
 * @param {string} password - User password.
 * @returns {Promise<Object>} User credential.
 * @example
 * const cred = await signUpUser(auth, 'newuser@example.com', 'password123');
 */
export async function signUpUser(auth, email, password) {
  if (!email || !password) {
    throw new Error('Email and password are required');
  }

  try {
    const userCredential = await auth.createUserWithEmailAndPassword(email, password);
    return userCredential;
  } catch (error) {
    console.error('Sign-up error:', error);
    throw error;
  }
}

/**
 * Signs out the current user.
 * @param {Object} auth - Firebase auth instance.
 * @returns {Promise<void>}
 * @example
 * await signOutUser(auth);
 */
export async function signOutUser(auth) {
  try {
    await auth.signOut();
  } catch (error) {
    console.error('Sign-out error:', error);
    throw error;
  }
}

export default {
  initializeFirebase,
  waitForAuthState,
  saveProfile,
  loadProfile,
  loadProfileNames,
  deleteProfile,
  signInUser,
  signUpUser,
  signOutUser
};
