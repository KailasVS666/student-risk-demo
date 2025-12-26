/**
 * Export Utilities Module
 * Handles CSV export functionality for assessment history.
 */

/**
 * Converts assessment history data to CSV format.
 * @param {Array<Object>} assessments - Array of assessment objects
 * @returns {string} CSV formatted string
 */
export function convertToCSV(assessments) {
  if (!assessments || assessments.length === 0) {
    return '';
  }

  // CSV Headers
  const headers = [
    'Profile Name',
    'Risk Level',
    'Confidence',
    'Timestamp',
    'School',
    'Age',
    'Sex',
    'Address',
    'Family Size',
    'Parent Status',
    'Mother Education',
    'Father Education',
    'Study Time',
    'Failures',
    'G1',
    'G2',
    'G3 (Predicted)',
    'Absences',
    'Health',
    'Activities',
    'Internet'
  ];

  // Build CSV rows
  const rows = assessments.map(assessment => {
    const data = assessment.data || {};
    return [
      `"${assessment.profileName || 'N/A'}"`,
      assessment.riskLevel || 'N/A',
      assessment.confidence ? `${(assessment.confidence * 100).toFixed(1)}%` : 'N/A',
      new Date(assessment.timestamp).toLocaleString(),
      data.school || 'N/A',
      data.age || 'N/A',
      data.sex || 'N/A',
      data.address || 'N/A',
      data.famsize || 'N/A',
      data.Pstatus || 'N/A',
      data.Medu || 'N/A',
      data.Fedu || 'N/A',
      data.studytime || 'N/A',
      data.failures || 'N/A',
      data.G1 || 'N/A',
      data.G2 || 'N/A',
      data.G3 || 'N/A',
      data.absences || 'N/A',
      data.health || 'N/A',
      data.activities || 'N/A',
      data.internet || 'N/A'
    ].join(',');
  });

  return [headers.join(','), ...rows].join('\n');
}

/**
 * Downloads data as a CSV file.
 * @param {string} csvContent - CSV formatted string
 * @param {string} filename - Name for the downloaded file
 */
export function downloadCSV(csvContent, filename = 'assessment_history.csv') {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  
  if (navigator.msSaveBlob) {
    // IE 10+
    navigator.msSaveBlob(blob, filename);
  } else {
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  }
}

/**
 * Exports assessment history to CSV file.
 * @param {Array<Object>} assessments - Array of assessment objects to export
 */
export function exportHistoryToCSV(assessments) {
  if (!assessments || assessments.length === 0) {
    console.warn('No assessments to export');
    return false;
  }

  try {
    const csvContent = convertToCSV(assessments);
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `student_assessments_${timestamp}.csv`;
    
    downloadCSV(csvContent, filename);
    console.log(`Exported ${assessments.length} assessments to ${filename}`);
    return true;
  } catch (error) {
    console.error('Failed to export CSV:', error);
    return false;
  }
}
