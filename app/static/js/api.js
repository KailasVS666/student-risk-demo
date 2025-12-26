/**
 * API Client Module
 * Handles all HTTP requests to the backend Flask API.
 */

import APP_CONFIG from './config.js';
import { showToast } from './ui-utils.js';
import { getCacheData, setCacheData } from './cache.js';
import { handleError, withErrorBoundary } from './error-handler.js';

/**
 * Makes a prediction request to the backend.
 * @param {Object} formData - The form data object containing student info.
 * @returns {Promise<Object>} The prediction response from the API.
 * @throws {Error} If the request fails.
 * @example
 * const result = await predictRisk(formData);
 * console.log(result.prediction, result.risk_category);
 */
export async function predictRisk(formData) {
  if (!formData || typeof formData !== 'object') {
    throw new Error('Invalid form data provided');
  }

  // Check cache first
  const cachedResult = getCacheData(APP_CONFIG.API.PREDICT, formData);
  if (cachedResult) {
    return cachedResult;
  }

  try {
    const response = await fetch(APP_CONFIG.API.PREDICT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(formData),
      credentials: 'same-origin' // Include cookies for CSRF
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || APP_CONFIG.MESSAGES.SERVER_ERROR);
    }

    // Validate response structure
    if (typeof data.prediction === 'undefined' || !data.risk_category) {
      throw new Error('Invalid response structure from prediction API');
    }

    // Cache successful response
    setCacheData(APP_CONFIG.API.PREDICT, formData, data);

    return data;
  } catch (error) {
    throw error;
  }
}

/**
 * Generates a PDF report from assessment results.
 * @param {Object} assessmentResults - The assessment results object.
 * @returns {Promise<Blob>} The PDF file blob.
 * @throws {Error} If PDF generation fails.
 * @example
 * const pdfBlob = await generatePDF(results);
 */
export async function generatePDF(assessmentResults) {
  if (!assessmentResults || typeof assessmentResults !== 'object') {
    throw new Error('Invalid assessment results');
  }

  try {
    const response = await fetch(APP_CONFIG.API.GENERATE_PDF, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(assessmentResults),
      credentials: 'same-origin' // Include cookies for CSRF
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || APP_CONFIG.MESSAGES.PDF_ERROR);
    }

    return await response.blob();
  } catch (error) {
    console.error('PDF generation error:', error);
    throw error;
  }
}

/**
 * Downloads a PDF blob as a file.
 * @param {Blob} pdfBlob - The PDF blob.
 * @param {string} [filename='report.pdf'] - The filename to use.
 * @example
 * downloadPDFFile(pdfBlob, 'student_report.pdf');
 */
export function downloadPDFFile(pdfBlob, filename = 'report.pdf') {
  try {
    const url = URL.createObjectURL(pdfBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `student_report_${Date.now()}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('PDF download error:', error);
    throw error;
  }
}

/**
 * Checks the health status of the backend service.
 * @returns {Promise<Object>} Health check response.
 * @example
 * const health = await checkHealth();
 * console.log(health.ok, health.models_loaded);
 */
export async function checkHealth() {
  try {
    const response = await fetch(APP_CONFIG.API.HEALTHZ, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Health check failed with status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Health check error:', error);
    throw error;
  }
}

/**
 * Gets the current status of loaded models.
 * @returns {Promise<Object>} Model status response.
 * @example
 * const status = await getModelStatus();
 * console.log(status.pipeline, status.label_encoder);
 */
export async function getModelStatus() {
  try {
    const response = await fetch(APP_CONFIG.API.STATUS, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Status check failed with status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Status check error:', error);
    throw error;
  }
}

/**
 * Generic fetch wrapper with error handling.
 * @param {string} url - The URL to fetch.
 * @param {Object} [options={}] - Fetch options.
 * @returns {Promise<Object>} The JSON response.
 * @throws {Error} If the request fails.
 * @private
 * @example
 * const data = await fetchAPI('/api/endpoint', { method: 'POST', body: JSON.stringify(...) });
 */
export async function fetchAPI(url, options = {}) {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      credentials: 'same-origin', // Include cookies
      ...options
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
    }

    return data;
  } catch (error) {
    console.error(`API error for ${url}:`, error);
    throw error;
  }
}

export default {
  predictRisk,
  generatePDF,
  downloadPDFFile,
  checkHealth,
  getModelStatus,
  fetchAPI
};
