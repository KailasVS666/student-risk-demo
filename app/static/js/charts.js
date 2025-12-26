/**
 * Chart Rendering Module
 * Manages all Chart.js visualizations (SHAP, grades, probabilities).
 */

import APP_CONFIG from './config.js';

// Global chart instances
let explanationChartInstance = null;
let gradesChartInstance = null;
let probaChartInstance = null;

/**
 * Destroys a chart instance if it exists.
 * @param {Chart|null} chartInstance - The chart instance to destroy.
 * @private
 */
function destroyChart(chartInstance) {
  if (chartInstance && typeof chartInstance.destroy === 'function') {
    chartInstance.destroy();
  }
}

/**
 * Filters out sensitive demographic features from SHAP values.
 * @param {Array<{feature: string, importance: number}>} shapValues - The SHAP values.
 * @param {boolean} showSensitive - Whether to show sensitive features.
 * @returns {Array<{feature: string, importance: number}>} Filtered SHAP values.
 * @example
 * const filtered = filterSensitiveFeatures(shapValues, false);
 */
export function filterSensitiveFeatures(shapValues, showSensitive = false) {
  if (showSensitive || !shapValues) {
    return shapValues || [];
  }

  return (shapValues || []).filter(item => {
    const featureName = (item.feature || '').toString().toLowerCase();
    return !APP_CONFIG.SENSITIVE_KEYWORDS.some(keyword => featureName.includes(keyword));
  });
}

/**
 * Renders the SHAP Feature Importance (Explanation) chart.
 * @param {Array<{feature: string, importance: number}>} shapValues - The SHAP values.
 * @param {boolean} [showSensitive=false] - Whether to show sensitive features.
 * @example
 * renderExplanationChart(shapData, false);
 */
export function renderExplanationChart(shapValues, showSensitive = false) {
  const chartCanvas = document.getElementById('explanationChart');
  if (!chartCanvas) {
    console.warn('Explanation chart canvas not found');
    return;
  }

  // Destroy previous instance
  destroyChart(explanationChartInstance);

  // Filter based on sensitivity setting
  const filteredValues = filterSensitiveFeatures(shapValues, showSensitive);

  // Update bias notice visibility
  const biasNotice = document.getElementById('biasNotice');
  if (biasNotice) {
    const filteredOutCount = (shapValues || []).length - (filteredValues || []).length;
    biasNotice.style.display = !showSensitive && filteredOutCount > 0 ? 'block' : 'none';
  }

  // Use filtered or original values
  const valuesToChart = filteredValues.length > 0 ? filteredValues : shapValues;

  if (!valuesToChart || valuesToChart.length === 0) {
    console.warn('No values to chart');
    return;
  }

  const features = valuesToChart.map(v => v.feature);
  const importances = valuesToChart.map(v => v.importance);
  const colors = importances.map(imp =>
    imp > 0 ? APP_CONFIG.CHARTS.EXPLANATION_POSITIVE_COLOR : APP_CONFIG.CHARTS.EXPLANATION_NEGATIVE_COLOR
  );

  const ctx = chartCanvas.getContext('2d');
  explanationChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: features,
      datasets: [
        {
          label: 'Impact on Risk Score',
          data: importances,
          backgroundColor: colors,
          borderColor: colors,
          borderWidth: 1
        }
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        x: {
          beginAtZero: false,
          title: {
            display: true,
            text: 'SHAP Value (Impact on Prediction)'
          }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (context) => context[0].label,
            label: (context) => {
              const value = context.parsed.x;
              const impact = value > 0 ? 'increases' : 'decreases';
              const sign = value > 0 ? '+' : '';
              return `Value: ${sign}${value.toFixed(2)}. This ${impact} the predicted risk.`;
            }
          }
        }
      }
    }
  });

  // Update textual summary
  updateShapSummary(valuesToChart);
}

/**
 * Updates the textual summary below the SHAP chart.
 * @param {Array<{feature: string, importance: number}>} valuesToChart - The SHAP values to summarize.
 * @private
 */
function updateShapSummary(valuesToChart) {
  const summaryEl = document.getElementById('shapSummary');
  if (!summaryEl) return;

  if (valuesToChart.length > 0) {
    const topFeature = valuesToChart[0].feature;
    const topImpact = valuesToChart[0].importance > 0 ? 'increase' : 'decrease';
    summaryEl.textContent =
      `Summary: The strongest factor influencing this prediction was the student's ${topFeature}, ` +
      `which is associated with a predicted ${topImpact} in risk level.`;
  } else {
    summaryEl.textContent = 'Summary: No non-sensitive factors were among the top contributors for this prediction.';
  }
}

/**
 * Renders the Grades Comparison chart (G1, G2, G3).
 * @param {number} G1 - First grade.
 * @param {number} G2 - Second grade.
 * @param {number} G3 - Predicted final grade.
 * @example
 * renderGradesChart(8, 9, 10);
 */
export function renderGradesChart(G1, G2, G3) {
  const chartCanvas = document.getElementById('gradesChart');
  if (!chartCanvas) {
    console.warn('Grades chart canvas not found');
    return;
  }

  // Destroy previous instance
  destroyChart(gradesChartInstance);

  const ctx = chartCanvas.getContext('2d');
  gradesChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['G1 (First Period)', 'G2 (Second Period)', 'G3 (Predicted Final)'],
      datasets: [
        {
          label: 'Student Grades (out of 20)',
          data: [G1, G2, G3],
          borderColor: APP_CONFIG.CHARTS.GRADES_LINE_COLOR,
          backgroundColor: APP_CONFIG.CHARTS.GRADES_FILL_COLOR,
          fill: true,
          tension: APP_CONFIG.CHARTS.CHART_TENSION,
          pointRadius: 5,
          pointBackgroundColor: APP_CONFIG.CHARTS.GRADES_LINE_COLOR
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        y: {
          beginAtZero: true,
          max: APP_CONFIG.CHARTS.GRADE_MAX,
          title: {
            display: true,
            text: 'Grade (out of 20)'
          }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: { mode: 'index', intersect: false }
      }
    }
  });
}

/**
 * Renders the Probability Distribution chart (class probabilities).
 * @param {Object} probMap - Probability map, e.g., {High: 0.12, Medium: 0.68, Low: 0.20}.
 * @example
 * renderProbaChart({ High: 0.1, Medium: 0.6, Low: 0.3 });
 */
export function renderProbaChart(probMap) {
  const chartCanvas = document.getElementById('probaChart');
  if (!chartCanvas) {
    console.warn('Probability chart canvas not found');
    return;
  }

  // Destroy previous instance
  destroyChart(probaChartInstance);

  if (!probMap || typeof probMap !== 'object') {
    console.warn('Invalid probability map');
    return;
  }

  const labelsOrder = APP_CONFIG.PROBABILITY_LABELS_ORDER;
  const dataValues = labelsOrder.map(label => (probMap[label] ?? 0) * 100);
  const colors = labelsOrder.map(label => {
    if (label === 'High') return APP_CONFIG.RISK_COLORS.high;
    if (label === 'Medium') return APP_CONFIG.RISK_COLORS.medium;
    return APP_CONFIG.RISK_COLORS.low;
  });

  const ctx = chartCanvas.getContext('2d');
  probaChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labelsOrder,
      datasets: [
        {
          label: 'Class Probability (%)',
          data: dataValues,
          backgroundColor: colors,
          borderColor: colors,
          borderWidth: 1
        }
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        x: {
          beginAtZero: true,
          max: 100,
          ticks: { callback: (value) => value + '%' }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => `${context.parsed.x.toFixed(1)}%`
          }
        }
      }
    }
  });
}

/**
 * Destroys all active chart instances.
 * Useful for cleanup when navigating away from results.
 * @example
 * destroyAllCharts();
 */
export function destroyAllCharts() {
  destroyChart(explanationChartInstance);
  destroyChart(gradesChartInstance);
  destroyChart(probaChartInstance);

  explanationChartInstance = null;
  gradesChartInstance = null;
  probaChartInstance = null;
}

/**
 * Gets references to all chart instances.
 * @returns {Object} Object containing chart instance references.
 * @private
 */
export function getChartInstances() {
  return {
    explanation: explanationChartInstance,
    grades: gradesChartInstance,
    probability: probaChartInstance
  };
}

export default {
  renderExplanationChart,
  renderGradesChart,
  renderProbaChart,
  filterSensitiveFeatures,
  destroyAllCharts,
  getChartInstances
};
