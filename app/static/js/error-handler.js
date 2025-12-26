/**
 * Error Handler Module
 * Centralized error handling with user-friendly messages and logging.
 */

import { showToast } from './ui-utils.js';

// Error categories
export const ERROR_TYPES = {
  NETWORK: 'network',
  VALIDATION: 'validation',
  API: 'api',
  AUTH: 'auth',
  UNKNOWN: 'unknown'
};

/**
 * Determines error type from error object.
 * @param {Error} error - Error object
 * @returns {string} Error type
 * @private
 */
function determineErrorType(error) {
  if (!error) return ERROR_TYPES.UNKNOWN;
  
  const message = error.message?.toLowerCase() || '';
  
  if (error.name === 'NetworkError' || message.includes('network') || message.includes('fetch')) {
    return ERROR_TYPES.NETWORK;
  }
  
  if (message.includes('validation') || message.includes('invalid')) {
    return ERROR_TYPES.VALIDATION;
  }
  
  if (message.includes('unauthorized') || message.includes('auth')) {
    return ERROR_TYPES.AUTH;
  }
  
  if (error.response) {
    return ERROR_TYPES.API;
  }
  
  return ERROR_TYPES.UNKNOWN;
}

/**
 * Gets user-friendly error message based on error type.
 * @param {string} errorType - Error type
 * @param {Error} error - Original error
 * @returns {string} User-friendly message
 * @private
 */
function getUserFriendlyMessage(errorType, error) {
  const messages = {
    [ERROR_TYPES.NETWORK]: 'Network connection issue. Please check your internet connection and try again.',
    [ERROR_TYPES.VALIDATION]: 'Please check your input and try again.',
    [ERROR_TYPES.API]: 'Server error occurred. Please try again in a moment.',
    [ERROR_TYPES.AUTH]: 'Authentication required. Please log in and try again.',
    [ERROR_TYPES.UNKNOWN]: 'An unexpected error occurred. Please try again.'
  };
  
  return error.message || messages[errorType] || messages[ERROR_TYPES.UNKNOWN];
}

/**
 * Handles errors with consistent logging and user feedback.
 * @param {Error} error - Error object
 * @param {Object} [options] - Error handling options
 * @param {string} [options.context] - Context where error occurred
 * @param {boolean} [options.showToast=true] - Whether to show toast notification
 * @param {Function} [options.onError] - Custom error handler callback
 * @returns {Object} Processed error info
 */
export function handleError(error, options = {}) {
  const {
    context = 'Application',
    showToastNotification = true,
    onError
  } = options;
  
  const errorType = determineErrorType(error);
  const userMessage = getUserFriendlyMessage(errorType, error);
  
  // Log error details (only in development)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.error(`[${context}] Error:`, {
      type: errorType,
      message: error.message,
      stack: error.stack,
      error
    });
  }
  
  // Show user notification
  if (showToastNotification) {
    showToast(userMessage, 'error');
  }
  
  // Call custom error handler if provided
  if (typeof onError === 'function') {
    onError(error, errorType);
  }
  
  return {
    type: errorType,
    message: userMessage,
    originalError: error
  };
}

/**
 * Creates an error boundary wrapper for async functions.
 * @param {Function} fn - Async function to wrap
 * @param {Object} [options] - Error handling options
 * @returns {Function} Wrapped function with error handling
 */
export function withErrorBoundary(fn, options = {}) {
  return async function(...args) {
    try {
      return await fn.apply(this, args);
    } catch (error) {
      return handleError(error, {
        context: options.context || fn.name || 'Function',
        ...options
      });
    }
  };
}

/**
 * Wraps a synchronous function with error handling.
 * @param {Function} fn - Function to wrap
 * @param {Object} [options] - Error handling options
 * @returns {Function} Wrapped function with error handling
 */
export function withErrorHandler(fn, options = {}) {
  return function(...args) {
    try {
      return fn.apply(this, args);
    } catch (error) {
      return handleError(error, {
        context: options.context || fn.name || 'Function',
        ...options
      });
    }
  };
}

/**
 * Logs error to external monitoring service (placeholder for future implementation).
 * @param {Error} error - Error to log
 * @param {Object} metadata - Additional metadata
 */
export function logErrorToMonitoring(error, metadata = {}) {
  // Placeholder for future integration with error monitoring services
  // (e.g., Sentry, Rollbar, LogRocket)
  
  // For now, just log to console in production
  if (window.location.hostname !== 'localhost') {
    console.error('Error logged:', {
      error: error.message,
      stack: error.stack,
      metadata,
      timestamp: new Date().toISOString()
    });
  }
}
