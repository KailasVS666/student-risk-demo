// =========================================================================
// UI/UX UTILITY FUNCTIONS (For 10/10 Experience)
// =========================================================================

/**
 * Shows a temporary, non-intrusive toast notification.
 * @param {string} message - The message to display.
 * @param {('success'|'error'|'info')} type - The type of toast.
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Add to container and show
    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    // Hide and remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        toast.addEventListener('transitionend', () => toast.remove());
    }, 3000);
}

/**
 * Manages the state of a primary button during an async operation.
 * @param {HTMLElement} button - The button element.
 * @param {boolean} isLoading - True to show spinner and disable, false otherwise.
 * @param {string} originalText - The original text to restore.
 */
function setButtonLoading(button, isLoading, originalText = 'Submit') {
    button.disabled = isLoading;
    if (isLoading) {
        button.innerHTML = `<span class="button-loader"></span>${button.id === 'generateAdviceBtn' ? 'Analyzing...' : 'Loading...'}`;
        button.dataset.originalText = originalText;
    } else {
        button.innerHTML = originalText || button.dataset.originalText;
    }
}


// =========================================================================
// WIZARD/FORM LOGIC
// =========================================================================

let currentStep = 0;
const formSteps = document.querySelectorAll('.form-step');
const progressSteps = document.querySelectorAll('.progress-step');
const progressBarContainer = document.querySelector('.progress-bar-container');
const nextBtn = document.getElementById('nextBtn');
const prevBtn = document.getElementById('prevBtn');
const generateAdviceBtn = document.getElementById('generateAdviceBtn');

// Helper to update range values visually
document.querySelectorAll('input[type="range"]').forEach(input => {
    const valueSpan = document.getElementById(input.id + 'Value');
    input.addEventListener('input', () => {
        valueSpan.textContent = input.value;
    });
});

// ---- Validation helpers ----
function addFieldError(inputEl, message) {
    if (!inputEl) return;
    inputEl.classList.add('ring-2', 'ring-red-300', 'border-red-500');
    // if an error element already exists, update it; else create
    const key = `error-for-${inputEl.id}`;
    let err = document.getElementById(key);
    if (!err) {
        err = document.createElement('p');
        err.id = key;
        err.className = 'text-xs text-red-600 mt-1';
        // insert right after the input element
        inputEl.parentElement.appendChild(err);
    }
    err.textContent = message || 'This field is required';
}

function clearFieldError(inputEl) {
    if (!inputEl) return;
    inputEl.classList.remove('ring-2', 'ring-red-300', 'border-red-500');
    const key = `error-for-${inputEl.id}`;
    const err = document.getElementById(key);
    if (err) err.remove();
}

function clearAllErrorsInStep(stepIndex) {
    const stepEl = formSteps[stepIndex];
    if (!stepEl) return;
    stepEl.querySelectorAll('input, select, textarea').forEach(el => clearFieldError(el));
}

/**
 * Client-side validation for the current step: checks required fields exist.
 * Returns true if validation passes; otherwise annotates fields and returns false.
 */
function validateStep(step) {
    const requiredByStep = {
        0: ['school','sex','age','address','famsize','Pstatus','famrel'],
        1: ['Medu','Fedu','Mjob','Fjob','studytime','reason','guardian','schoolsup','famsup','paid','higher'],
        2: ['activities','nursery','internet','romantic','traveltime','freetime','goout','Dalc','Walc','health','absences','failures','G1','G2']
    };

    clearAllErrorsInStep(step);

    const ids = requiredByStep[step] || [];
    let firstInvalid = null;
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        let valid = true;
        if (el.tagName === 'SELECT' || el.type === 'text' || el.type === 'textarea') {
            valid = (el.value ?? '').toString().trim().length > 0;
        } else if (el.type === 'range' || el.type === 'number') {
            valid = (el.value ?? '') !== '' && !Number.isNaN(Number(el.value));
        } else {
            valid = (el.value ?? '') !== '';
        }
        if (!valid) {
            addFieldError(el, 'Please provide a value');
            if (!firstInvalid) firstInvalid = el;
        }
    });

    if (firstInvalid) {
        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
        showToast('Please complete the highlighted fields before continuing.', 'error');
        return false;
    }

    // Optional: specific check on step 2 for G1/G2 minimum sensible values
    if (step === 2) {
        const g1 = Number(document.getElementById('G1')?.value ?? 0);
        const g2 = Number(document.getElementById('G2')?.value ?? 0);
        if (g1 < 0 || g2 < 0) {
            addFieldError(document.getElementById('G1'), 'Must be >= 0');
            addFieldError(document.getElementById('G2'), 'Must be >= 0');
            showToast('Grades must be zero or positive.', 'error');
            return false;
        }
    }
    return true;
}

function updateWizard() {
    // 1. Update Form Visibility
    formSteps.forEach((step, index) => {
        step.classList.toggle('active-step', index === currentStep);
    });

    // 2. Update Progress Steps
    progressSteps.forEach((step, index) => {
        step.classList.toggle('active', index === currentStep);
        // Mark previous steps as complete (visually handled by the line CSS)
        if (index < currentStep) {
             step.classList.add('completed');
        } else {
             step.classList.remove('completed');
        }
    });

    // 3. Update Progress Bar Line Animation (CSS Classes)
    progressBarContainer.classList.remove('step-2', 'step-3');
    if (currentStep >= 1) {
        progressBarContainer.classList.add('step-2');
    }
    if (currentStep >= 2) {
        progressBarContainer.classList.add('step-3');
    }

    // 4. Update Navigation Buttons
    prevBtn.style.display = currentStep > 0 ? 'inline-flex' : 'none';

    if (currentStep === formSteps.length - 1) {
        // Last step
        nextBtn.style.display = 'none';
        generateAdviceBtn.disabled = false;
    } else {
        // Middle steps
        nextBtn.style.display = 'inline-flex';
        generateAdviceBtn.disabled = true;
    }
}

nextBtn.addEventListener('click', () => {
    if (!validateStep(currentStep)) return;
    currentStep++;
    updateWizard();
});

prevBtn.addEventListener('click', () => {
    if (currentStep > 0) {
        currentStep--;
        updateWizard();
    }
});

// Initialize the wizard on load
updateWizard();

// Clear errors when user edits fields
document.querySelectorAll('#inputForm input, #inputForm select, #inputForm textarea').forEach(el => {
    el.addEventListener('input', () => clearFieldError(el));
    el.addEventListener('change', () => clearFieldError(el));
});


// =========================================================================
// RESULTS & API INTERACTION LOGIC
// =========================================================================

// Placeholder for chart instances to allow easy destruction/update
let explanationChartInstance = null;
let gradesChartInstance = null;
let probaChartInstance = null;
// Keep the raw SHAP values from the backend so we can re-render when toggling sensitive features
let lastShapValuesRaw = null;

// The main function to handle prediction and advice generation
document.getElementById('generateAdviceBtn').addEventListener('click', async () => {
    // Gather form data (including the custom prompt)
    const formData = gatherFormData();
    if (!formData) return; // Basic check

    // 1. UI State: Show Loading, Hide Results
    document.getElementById('resultsSection').classList.remove('hidden');
    document.getElementById('loadingSpinner').classList.remove('hidden');
    document.getElementById('adviceContent').classList.add('hidden');
    document.getElementById('explanationChartContainer').classList.add('hidden');
    setButtonLoading(generateAdviceBtn, true, 'Generate Mentoring Advice');

    try {
        // 2. API Call 
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();

        // 3. Handle Errors
        if (!response.ok) {
            throw new Error(data.error || 'Prediction failed due to server error.');
        }

        // 4. UI State: Hide Loading
        document.getElementById('loadingSpinner').classList.add('hidden');
        document.getElementById('adviceContent').classList.remove('hidden');
        document.getElementById('explanationChartContainer').classList.remove('hidden');
        showToast('Analysis complete!', 'success');

        // 5. Update Risk Badge (CRITICAL UX IMPROVEMENT)
        updateRiskBadge(data.risk_category, data.prediction, data.confidence); // risk_category is 'low'|'medium'|'high'

        // 6. Render Advice (Structure the output for 10/10 UX)
        renderAdvice(data.mentoring_advice); // This should handle structured/markdown advice

        // 7. Render Charts
        if (data.probabilities) {
            renderProbaChart(data.probabilities);
        }
        // Save raw SHAP values and render with current toggle state
        lastShapValuesRaw = data.shap_values || [];
        renderExplanationChart(lastShapValuesRaw);
        renderGradesChart(formData.G1, formData.G2, data.prediction); // Pass G1, G2, and final prediction

    } catch (error) {
        console.error('Prediction Error:', error);
        showToast(`Error: ${error.message || 'Could not connect to the analysis engine.'}`, 'error');
        // Restore UI state on error
        document.getElementById('loadingSpinner').classList.add('hidden');
        document.getElementById('adviceContent').classList.add('hidden');
        document.getElementById('resultsSection').classList.remove('hidden'); // Keep section visible to show the error
    } finally {
        setButtonLoading(generateAdviceBtn, false);
    }
});


/**
 * Gathers all form data into a structured object AND CALCULATES ENGINEERED FEATURES.
 */
function gatherFormData() {
    const data = {};
    let g1_score = 0;
    let g2_score = 0;

    document.querySelectorAll('#inputForm select, #inputForm input').forEach(input => {
        // Use the ID as the key (e.g., 'age', 'school', 'Medu')
        if (input.type === 'range') {
             const value = parseInt(input.value);
             data[input.id] = value;
             
             // Capture G1 and G2 for engineered features
             if (input.id === 'G1') g1_score = value;
             if (input.id === 'G2') g2_score = value;
        } else {
             // Select and other inputs are strings
             data[input.id] = input.value;
        }
    });

    // CRITICAL FIX: Add the two missing engineered features required by the ML model pipeline
    data.average_grade = (g1_score + g2_score) / 2;
    data.grade_change = g2_score - g1_score;
    
    // FIX: Include the custom prompt in the payload
    data.customPrompt = document.getElementById('customPrompt').value.trim();

    return data;
}

/**
 * Dynamically updates the Risk Level Badge color and text.
 * @param {string} category - 'low', 'medium', or 'high'.
 * @param {number} finalGrade - The predicted final grade (G3).
 */
function updateRiskBadge(category, finalGrade, confidence) {
    const badge = document.getElementById('riskLevelBadge');
    const levelText = document.getElementById('riskLevel');
    const descriptor = document.getElementById('riskDescriptor');
    const confText = document.getElementById('riskConfidence');

    // Reset classes
    badge.className = 'p-4 rounded-xl shadow-lg text-center transition duration-500';

    switch (category.toLowerCase()) {
        case 'low':
            badge.classList.add('risk-low');
            levelText.textContent = 'Low Risk';
            descriptor.textContent = `Predicted Final Grade (G3): ${finalGrade}`;
            break;
        case 'medium':
            badge.classList.add('risk-medium');
            levelText.textContent = 'Medium Risk';
            descriptor.textContent = `Predicted Final Grade (G3): ${finalGrade}`;
            break;
        case 'high':
        default:
            badge.classList.add('risk-high');
            levelText.textContent = 'High Risk';
            descriptor.textContent = `Predicted Final Grade (G3): ${finalGrade}`;
            break;
    }

    if (confText) {
        const pct = typeof confidence === 'number' ? Math.round(confidence * 100) : null;
        confText.textContent = pct !== null ? `Model confidence: ${pct}% for this risk class` : '';
    }
}

/**
 * Renders the AI advice, handling basic markdown for structure.
 * @param {string} adviceText - The text from the API, possibly with Markdown-like formatting.
 */
function renderAdvice(adviceText) {
    const outputDiv = document.getElementById('adviceOutput');
    
    // Convert markdown headers (###) to <h3> tags
    let htmlContent = adviceText.replace(/###\s+(.*)/g, '<h3>$1</h3>');
    
    // Convert strong text (**text**) to <strong> for better prose styling
    htmlContent = htmlContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Simple conversion of markdown lists to HTML lists
    htmlContent = htmlContent
        .replace(/\*\s/g, '<li>') // Convert '*' bullets to list items
        .replace(/\n\n/g, '<p>')  // Convert double newlines to paragraphs
        .replace(/\n/g, '<br>');  // Convert single newlines to breaks

    // Wrap list items in <ul> if present (simple check)
    outputDiv.innerHTML = htmlContent;
}


/**
 * Initializes/updates the Key Factors chart (SHAP values).
 * @param {object} shapValues - The feature importance data.
 */
function renderExplanationChart(shapValues) {
    if (explanationChartInstance) {
        explanationChartInstance.destroy();
    }

    // Filter sensitive features based on toggle state
    const toggle = document.getElementById('toggleSensitive');
    const biasNotice = document.getElementById('biasNotice');
    const showSensitive = toggle ? toggle.checked : false;
    const filtered = filterSensitiveFeatures(shapValues, showSensitive);

    // Show a notice if sensitive features were hidden and at least one was filtered out
    if (biasNotice) {
        const filteredOutCount = shapValues.length - filtered.length;
        biasNotice.style.display = (!showSensitive && filteredOutCount > 0) ? 'block' : 'none';
    }

    // Use filtered values for charting
    const valuesForChart = filtered.length > 0 ? filtered : shapValues;

    // Assuming shapValues is an array of { feature: string, importance: number }
    const features = valuesForChart.map(f => f.feature);
    const importance = valuesForChart.map(f => f.importance);
    const backgroundColors = importance.map(i => i > 0 ? '#10B981' : '#EF4444'); // Green for positive impact, Red for negative

    const ctx = document.getElementById('explanationChart').getContext('2d');
    explanationChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: features,
            datasets: [{
                label: 'Impact on Risk Score',
                data: importance,
                backgroundColor: backgroundColors,
                borderColor: backgroundColors,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y', // Horizontal bars
            responsive: true,
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
                             // A brief, non-technical explanation based on impact
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

    // Simple textual summary (UX enhancement)
    const summaryEl = document.getElementById('shapSummary');
    if (valuesForChart.length > 0) {
        const topFeature = valuesForChart[0].feature;
        const topImpact = valuesForChart[0].importance > 0 ? 'increase' : 'decrease';
        summaryEl.textContent = `Summary: The strongest factor influencing this prediction was the student's ${topFeature}, which is associated with a predicted ${topImpact} in risk level.`;
    } else {
        summaryEl.textContent = 'Summary: No non-sensitive factors were among the top contributors for this prediction.';
    }
}

/**
 * Filters out sensitive features from SHAP results when showSensitive is false.
 * Sensitivity heuristic matches on common attribute names in the display string.
 * @param {Array<{feature:string, importance:number}>} shapValues
 * @param {boolean} showSensitive
 */
function filterSensitiveFeatures(shapValues, showSensitive) {
    if (showSensitive) return shapValues || [];
    const sensitiveKeywords = ['sex', 'gender', 'age', 'guardian', 'address', 'famsize', 'pstatus', 'mjob', 'fjob', 'romantic'];
    return (shapValues || []).filter(item => {
        const name = (item.feature || '').toString().toLowerCase();
        return !sensitiveKeywords.some(kw => name.includes(kw));
    });
}

/**
 * Initializes/updates the Grades Comparison chart.
 * @param {number} G1 - First Grade.
 * @param {number} G2 - Second Grade.
 * @param {number} G3 - Predicted Final Grade.
 */
function renderGradesChart(G1, G2, G3) {
    if (gradesChartInstance) {
        gradesChartInstance.destroy();
    }
    
    const ctx = document.getElementById('gradesChart').getContext('2d');
    gradesChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['G1 (First Period)', 'G2 (Second Period)', 'G3 (Predicted Final)'],
            datasets: [{
                label: 'Student Grades (out of 20)',
                data: [G1, G2, G3],
                borderColor: '#4F46E5', // Indigo-600
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 20
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
 * Renders a small probability bar chart for classes.
 * @param {object} probMap - e.g., { High: 0.12, Medium: 0.68, Low: 0.20 }
 */
function renderProbaChart(probMap) {
    if (probaChartInstance) {
        probaChartInstance.destroy();
    }

    const labelsOrder = ['High', 'Medium', 'Low'];
    const dataVals = labelsOrder.map(k => (probMap[k] ?? 0) * 100);
    const colors = labelsOrder.map(k => k === 'High' ? '#EF4444' : k === 'Medium' ? '#F59E0B' : '#10B981');

    const ctx = document.getElementById('probaChart').getContext('2d');
    probaChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labelsOrder,
            datasets: [{
                label: 'Class Probability (%)',
                data: dataVals,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            scales: {
                x: { beginAtZero: true, max: 100, ticks: { callback: (v) => v + '%' } }
            },
            plugins: { legend: { display: false } }
        }
    });
}


// =========================================================================
// FIREBASE AND AUTHENTICATION LOGIC (FULLY FIXED)
// =========================================================================
(function() {

    if (typeof firebase === 'undefined' || typeof FIREBASE_CONFIG === 'undefined') {
        console.error("Firebase SDK or FIREBASE_CONFIG is missing. App cannot start.");
        showToast("Error: Firebase config missing.", 'error');
        return;
    }
    
    let config = FIREBASE_CONFIG;
    if (typeof config === 'string') {
        try {
            config = JSON.parse(config);
        } catch (e) {
            console.error("Error parsing FIREBASE_CONFIG string:", e);
            showToast("Error initializing Firebase config.", 'error');
            return;
        }
    }
    
    if (!config || !config.projectId) {
        console.error("Firebase config missing projectId.");
        showToast("Firebase project ID missing. Save/Load disabled.", 'error');
        return;
    }

    // --- Initialize Firebase Services ---
    if (!firebase.apps.length) {
        firebase.initializeApp(config);
        console.log("Firebase initialized successfully.");
    }
    const db = firebase.firestore();
    const auth = firebase.auth();

    // --- Get UI Elements ---
    const authContainer = document.getElementById('auth-container');
    const appContainer = document.getElementById('app');
    const userEmailSpan = document.getElementById('user-email');
    const authError = document.getElementById('auth-error');

    // --- Auth State Variable ---
    let userEmail = null; // This will be set to the *actual* logged-in user's email

    // --- PRIMARY AUTHENTICATION LISTENER ---
    // This function runs on page load and whenever login state changes
    auth.onAuthStateChanged(user => {
        if (user) {
            // User is SIGNED IN
            userEmail = user.email;
            userEmailSpan.textContent = userEmail;
            
            // Show the app, hide the login form
            appContainer.classList.remove('hidden');
            authContainer.classList.add('hidden');
            
            // IMPORTANT: Load profiles *after* we know who the user is
            loadProfiles();

        } else {
            // User is SIGNED OUT
            userEmail = null;
            userEmailSpan.textContent = '';
            
            // Show the login form, hide the app
            appContainer.classList.add('hidden');
            authContainer.classList.remove('hidden');
        }
    });

    // --- Auth Form Listeners ---
    document.getElementById('loginBtn').addEventListener('click', () => {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        authError.textContent = ''; // Clear previous errors

        auth.signInWithEmailAndPassword(email, password)
            .then(userCredential => {
                showToast('Logged in successfully!', 'success');
                // onAuthStateChanged will handle hiding the form
            })
            .catch(error => {
                authError.textContent = error.message;
            });
    });

    document.getElementById('signupBtn').addEventListener('click', () => {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        authError.textContent = ''; // Clear previous errors

        auth.createUserWithEmailAndPassword(email, password)
            .then(userCredential => {
                showToast('Account created! You are now logged in.', 'success');
                // onAuthStateChanged will handle hiding the form
            })
            .catch(error => {
                authError.textContent = error.message;
            });
    });

    // --- Logout Button ---
    document.getElementById('logoutBtn').addEventListener('click', () => {
        auth.signOut().then(() => {
            showToast('Logged out successfully.', 'info');
            // onAuthStateChanged will automatically show the login screen
        }).catch((error) => {
            console.error("Logout Error:", error);
            showToast('Error logging out.', 'error');
        });
    });


    // --- Profile Save/Load Handlers (Now use the correct userEmail) ---

    document.getElementById('saveProfileBtn').addEventListener('click', async () => {
        const saveBtn = document.getElementById('saveProfileBtn');
        if (!userEmail) {
            showToast('You must be logged in to save a profile.', 'error');
            return;
        }
        
        const profileName = document.getElementById('profileName').value.trim();
        if (!profileName) {
            showToast('Please enter a name for the profile.', 'error');
            return;
        }
        
        const profileData = gatherFormData();

        try {
            // UI: prevent double submits
            if (saveBtn) { saveBtn.disabled = true; saveBtn.dataset.originalText = saveBtn.innerText; saveBtn.innerText = 'Saving...'; }
            // This now correctly uses the logged-in user's email
            const docRef = db.collection('profiles')
                .doc(userEmail)
                .collection('student_data')
                .doc(profileName);

            const existing = await docRef.get();
            if (existing.exists) {
                await docRef.set({
                    ...profileData,
                    updatedAt: firebase.firestore.FieldValue.serverTimestamp()
                }, { merge: true });
            } else {
                await docRef.set({
                    ...profileData,
                    createdAt: firebase.firestore.FieldValue.serverTimestamp(),
                    updatedAt: firebase.firestore.FieldValue.serverTimestamp()
                }, { merge: true });
            }
            showToast(`Profile \"${profileName}\" saved successfully!`, 'success');
            loadProfiles(); // Refresh the dropdown
            window.__formDirty = false; // reset unsaved changes flag
        } catch (error) {
            console.error("Error saving profile: ", error);
            showToast('Error saving profile.', 'error');
        } finally {
            if (saveBtn) { saveBtn.disabled = false; saveBtn.innerText = saveBtn.dataset.originalText || 'Save Profile'; }
        }
    });

    document.getElementById('loadProfileBtn').addEventListener('click', async (e) => {
        const btn = e.currentTarget;
        const selectedProfileName = document.getElementById('loadProfileSelect').value;
        if (!selectedProfileName) {
            showToast('Please select a profile to load.', 'info');
            return;
        }
        try {
            btn.disabled = true;
            btn.dataset.originalText = btn.innerText;
            btn.innerText = 'Loading...';
            await loadProfile(selectedProfileName);
        } finally {
            btn.disabled = false;
            btn.innerText = btn.dataset.originalText || 'Load Profile';
        }
    });


    /**
     * Fetches the list of saved profiles and populates the dropdown.
     */
    async function loadProfiles() {
        const select = document.getElementById('loadProfileSelect');
        select.innerHTML = '<option value="">- Select a profile -</option>'; // Clear

        if (!userEmail) return; // Don't run if user is logged out

        try {
            // This now correctly loads from the logged-in user's collection
            const snapshot = await db.collection('profiles').doc(userEmail).collection('student_data').get();
            
            if (snapshot.empty) {
                console.log("No saved profiles found for this user.");
                return;
            }

            snapshot.forEach(doc => {
                const option = document.createElement('option');
                option.value = doc.id;
                option.textContent = doc.id;
                select.appendChild(option);
            });
            showToast('Saved profiles loaded.', 'info');
        } catch (error) {
            console.error("Error loading profiles: ", error);
            // This error will happen if Firestore rules are not set correctly
            showToast('Could not load profiles (check permissions).', 'error');
        }
    }

    /**
     * Loads a specific profile's data into the form inputs.
     * @param {string} profileName - The name of the profile to load.
     */
    async function loadProfile(profileName) {
        if (!userEmail) return;

        try {
            const doc = await db.collection('profiles').doc(userEmail).collection('student_data').doc(profileName).get();
            if (doc.exists) {
                const data = doc.data();
                
                for (const key in data) {
                    const input = document.getElementById(key);
                    if (input) {
                        if (input.tagName === 'SELECT') {
                            input.value = data[key];
                        } 
                        else if (input.type === 'range') {
                            input.value = data[key];
                            const valueSpan = document.getElementById(key + 'Value');
                            if (valueSpan) valueSpan.textContent = data[key];
                        }
                        else if (input.tagName === 'TEXTAREA' && key === 'customPrompt') {
                            input.value = data[key];
                        }
                    }
                }
                // Set the profile name in the input box
                document.getElementById('profileName').value = profileName;
                showToast(`Profile "${profileName}" loaded!`, 'success');
            } else {
                showToast(`Profile "${profileName}" not found.`, 'error');
            }
        } catch (error) {
            console.error("Error loading profile: ", error);
            showToast('Error loading profile.', 'error');
        }
    }

    // --- Misc Button Wrappers ---

    document.getElementById('clearFormBtn').addEventListener('click', () => {
        document.querySelectorAll('#inputForm select').forEach(select => select.selectedIndex = 0);
        document.querySelectorAll('#inputForm input[type="range"]').forEach(range => {
            range.value = range.getAttribute('value'); // Reset to default
            const valueSpan = document.getElementById(range.id + 'Value');
            if (valueSpan) valueSpan.textContent = range.value;
        });
        document.getElementById('customPrompt').value = '';
        document.getElementById('profileName').value = 'new_student';
        showToast('Form cleared.', 'info');
    });

    document.getElementById('copyAdviceBtn').addEventListener('click', () => {
        const adviceText = document.getElementById('adviceOutput').innerText;
        if (adviceText) {
            navigator.clipboard.writeText(adviceText);
            showToast('Advice copied to clipboard!', 'info');
        }
    });

})();

// =========================================================================
// SENSITIVE FEATURE TOGGLE BINDING
// =========================================================================
document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('toggleSensitive');
    if (toggle) {
        toggle.addEventListener('change', () => {
            if (lastShapValuesRaw) {
                renderExplanationChart(lastShapValuesRaw);
            }
        });
    }
    // Unsaved changes guard for assessment form
    const inputForm = document.getElementById('inputForm');
    if (inputForm) {
        window.__formDirty = false;
        inputForm.addEventListener('input', () => { window.__formDirty = true; });
        window.addEventListener('beforeunload', (e) => {
            if (window.__formDirty) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
        const submitBtn = document.getElementById('generateAdviceBtn');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => { window.__formDirty = false; });
        }
        const clearBtn = document.getElementById('clearFormBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => { window.__formDirty = false; });
        }
    }
});