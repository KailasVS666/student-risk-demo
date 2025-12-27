/**
 * Results Rendering Module
 * Handles rendering of prediction results, risk badges, and mentoring advice.
 */

import APP_CONFIG from './config.js';

/**
 * Updates the risk level badge with category, grade, and confidence.
 * @param {string} category - Risk category ('low', 'medium', 'high').
 * @param {number} finalGrade - Predicted final grade.
 * @param {number} confidence - Model confidence (0-1 or 0-100).
 * @example
 * updateRiskBadge('high', 8, 0.85);
 */
export function updateRiskBadge(category, finalGrade, confidence) {
  const badge = document.getElementById('riskBadge');
  const levelText = document.getElementById('riskLevel');
  const descriptor = document.getElementById('riskDescriptor');
  const confText = document.getElementById('confidenceText');

  if (!badge || !levelText) {
    console.warn('Risk badge elements not found in DOM');
    return;
  }

  // Clear previous risk classes
  badge.classList.remove('risk-high', 'risk-medium', 'risk-low');

  // Ensure final grade is a number
  const gradeValue = typeof finalGrade === 'number' ? Math.round(finalGrade) : finalGrade;

  // Set new risk class and text
  const normalizedCategory = (category || '').toLowerCase();

  switch (normalizedCategory) {
    case APP_CONFIG.RISK_LEVELS.LOW:
      badge.classList.add('risk-low');
      levelText.textContent = 'Low Risk';
      if (descriptor) {
        descriptor.textContent = `Predicted Final Grade (G3): ${gradeValue}`;
      }
      break;

    case APP_CONFIG.RISK_LEVELS.MEDIUM:
      badge.classList.add('risk-medium');
      levelText.textContent = 'Medium Risk';
      if (descriptor) {
        descriptor.textContent = `Predicted Final Grade (G3): ${gradeValue}`;
      }
      break;

    case APP_CONFIG.RISK_LEVELS.HIGH:
    default:
      badge.classList.add('risk-high');
      levelText.textContent = 'High Risk';
      if (descriptor) {
        descriptor.textContent = `Predicted Final Grade (G3): ${gradeValue}`;
      }
      break;
  }

  // Update confidence text
  if (confText && typeof confidence === 'number') {
    const percentage = confidence <= 1 ? Math.round(confidence * 100) : Math.round(confidence);
    confText.textContent = `Model confidence: ${percentage}% for this risk class`;
  }
}

/**
 * Renders mentoring advice with markdown-like formatting.
 * @param {string} adviceText - The advice text (may contain markdown-like formatting).
 * @example
 * renderAdvice(data.mentoring_advice);
 */
export function renderAdvice(adviceText) {
  const outputDiv = document.getElementById('adviceOutput');

  if (!outputDiv) {
    console.warn('Advice output element not found');
    return;
  }

  if (!adviceText || typeof adviceText !== 'string') {
    outputDiv.innerHTML = '<p>No advice available.</p>';
    return;
  }

  const lines = adviceText.split('\n');
  const htmlParts = [];
  let inList = false;

  const closeList = () => {
    if (inList) {
      htmlParts.push('</ul>');
      inList = false;
    }
  };

  lines.forEach(rawLine => {
    const line = rawLine.trim();

    if (!line) {
      closeList();
      return;
    }

    const headingMatch = line.match(/^#{2,3}\s+(.*)/);
    if (headingMatch) {
      closeList();
      htmlParts.push(`<h3>${formatInline(headingMatch[1])}</h3>`);
      return;
    }

    if (line.startsWith('>')) {
      closeList();
      const noteText = line.replace(/^>\s?/, '');
      htmlParts.push(`<p class="advice-note">${formatInline(noteText)}</p>`);
      return;
    }

    const bulletMatch = line.match(/^[-*]\s+(.*)/);
    if (bulletMatch) {
      if (!inList) {
        htmlParts.push('<ul>');
        inList = true;
      }
      htmlParts.push(`<li>${formatInline(bulletMatch[1])}</li>`);
      return;
    }

    closeList();
    htmlParts.push(`<p>${formatInline(line)}</p>`);
  });

  closeList();

  outputDiv.innerHTML = htmlParts.join('');

  // Sanitization: remove any script tags or dangerous attributes
  sanitizeHTML(outputDiv);
}

function formatInline(text) {
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  return escaped
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

/**
 * Basic HTML sanitization to prevent XSS.
 * Removes script tags and potentially dangerous attributes.
 * @param {HTMLElement} element - The element to sanitize.
 * @private
 */
function sanitizeHTML(element) {
  // Remove script tags
  element.querySelectorAll('script').forEach(script => script.remove());

  // Remove event handlers and dangerous attributes
  element.querySelectorAll('*').forEach(el => {
    Array.from(el.attributes).forEach(attr => {
      if (attr.name.startsWith('on') || attr.name === 'href' || attr.name === 'src') {
        // Only remove if suspicious
        if (attr.value && (attr.value.includes('javascript:') || attr.value.includes('data:'))) {
          el.removeAttribute(attr.name);
        }
      }
    });
  });
}

/**
 * Updates DOM with assessment results and shows results section.
 * @param {Object} results - The assessment results object.
 * @example
 * displayResults({
 *   prediction: 10,
 *   risk_category: 'medium',
 *   confidence: 0.75,
 *   mentoring_advice: '...',
 *   shap_values: [...],
 *   probabilities: {...}
 * });
 */
export function displayResults(results) {
  if (!results || typeof results !== 'object') {
    console.error('Invalid results object');
    return;
  }

  // Update risk badge
  updateRiskBadge(results.risk_category, results.prediction, results.confidence);

  // Render advice
  if (results.mentoring_advice) {
    renderAdvice(results.mentoring_advice);
  }

  // Show results section
  const resultsSection = document.getElementById('resultsSection');
  const adviceContent = document.getElementById('adviceContent');

  if (resultsSection) {
    resultsSection.classList.remove('hidden');
  }

  if (adviceContent) {
    adviceContent.classList.remove('hidden');
  }
}

/**
 * Clears all rendered results and hides results section.
 * @example
 * clearResults();
 */
export function clearResults() {
  const resultsSection = document.getElementById('resultsSection');
  const adviceOutput = document.getElementById('adviceOutput');
  const riskBadge = document.getElementById('riskBadge');

  if (resultsSection) {
    resultsSection.classList.add('hidden');
  }

  if (adviceOutput) {
    adviceOutput.innerHTML = '';
  }

  if (riskBadge) {
    riskBadge.classList.remove('risk-high', 'risk-medium', 'risk-low');
  }
}

/**
 * Gets a readable name for a feature.
 * @param {string} featureName - The internal feature name.
 * @returns {string} The readable feature name.
 * @example
 * getReadableFeatureName('G1') => 'First Grade'
 */
export function getReadableFeatureName(featureName) {
  return APP_CONFIG.READABLE_FEATURE_NAMES[featureName] || featureName;
}

/**
 * Formats a confidence value as a percentage string.
 * @param {number} confidence - Confidence value (0-1 or 0-100).
 * @returns {string} Formatted percentage string.
 * @example
 * formatConfidencePercentage(0.85) => '85%'
 */
export function formatConfidencePercentage(confidence) {
  if (typeof confidence !== 'number') {
    return 'N/A';
  }

  const percentage = confidence <= 1 ? Math.round(confidence * 100) : Math.round(confidence);
  return `${percentage}%`;
}

/**
 * Gets a color code for a risk level.
 * @param {string} riskLevel - Risk level ('low', 'medium', 'high').
 * @returns {string} Hex color code.
 * @example
 * getRiskColor('high') => '#EF4444'
 */
export function getRiskColor(riskLevel) {
  const normalized = (riskLevel || '').toLowerCase();
  return APP_CONFIG.RISK_COLORS[normalized] || APP_CONFIG.RISK_COLORS.medium;
}

export default {
  updateRiskBadge,
  renderAdvice,
  displayResults,
  clearResults,
  getReadableFeatureName,
  formatConfidencePercentage,
  getRiskColor
};
