async function initializeFirebase() {
    try {
        const response = await fetch('/firebase-config');
        if (!response.ok) {
            throw new Error('Could not fetch Firebase config from server.');
        }
        const firebaseConfig = await response.json();
        const firebaseApp = firebase.initializeApp(firebaseConfig);
        const db = firebase.firestore();
        const auth = firebase.auth();
        
        runApp(db, auth);

    } catch (error) {
        console.error("Firebase initialization failed:", error);
        alert("Could not connect to the database. Please check the console for errors.");
    }
}

// --- NEW: Toast Notification Function ---
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 500);
        }, 3000);
    }, 100);
}

function runApp(db, auth) {
    // --- Element selections ---
    const authContainer = document.getElementById('auth-container');
    const appContainer = document.getElementById('app');
    const authError = document.getElementById('auth-error');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const loginBtn = document.getElementById('loginBtn');
    const signupBtn = document.getElementById('signupBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const userEmailSpan = document.getElementById('user-email');
    const resultsSection = document.getElementById('resultsSection');
    const generateAdviceBtn = document.getElementById('generateAdviceBtn');
    const saveProfileBtn = document.getElementById('saveProfileBtn');
    const loadProfileBtn = document.getElementById('loadProfileBtn');
    const loadProfileSelect = document.getElementById('loadProfileSelect');
    const copyAdviceBtn = document.getElementById('copyAdviceBtn');
    const clearFormBtn = document.getElementById('clearFormBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const shapSummaryDiv = document.getElementById('shapSummary');
    const customPromptInput = document.getElementById('customPrompt');

    let currentUser = null;
    let explanationChart = null; 
    let gradesChart = null;
    
    // --- Wizard elements and state ---
    let currentStep = 0;
    const formSteps = document.querySelectorAll('.form-step');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const progressSteps = document.querySelectorAll('.progress-step');
    const progressLines = document.querySelectorAll('.progress-line');

    // --- Authentication Logic ---
    auth.onAuthStateChanged(user => {
        if (user) {
            currentUser = user;
            authContainer.classList.add('hidden');
            appContainer.classList.remove('hidden');
            userEmailSpan.textContent = user.email;
            fetchProfiles();
        } else {
            currentUser = null;
            authContainer.classList.remove('hidden');
            appContainer.classList.add('hidden');
            loadProfileSelect.innerHTML = '<option value="">- Select a profile -</option>';
        }
    });

    signupBtn.addEventListener('click', () => {
        const email = emailInput.value;
        const password = passwordInput.value;
        auth.createUserWithEmailAndPassword(email, password)
            .catch(error => { authError.textContent = error.message; });
    });

    loginBtn.addEventListener('click', () => {
        const email = emailInput.value;
        const password = passwordInput.value;
        auth.signInWithEmailAndPassword(email, password)
            .catch(error => { authError.textContent = error.message; });
    });

    logoutBtn.addEventListener('click', () => {
        auth.signOut();
    });

    // --- Application Logic ---
    const sliderIds = [
        'age', 'Medu', 'Fedu', 'traveltime', 'studytime', 'failures', 
        'famrel', 'freetime', 'goout', 'Dalc', 'Walc', 'health', 'absences', 'G1', 'G2'
    ];
      
    sliderIds.forEach(id => {
        const slider = document.getElementById(id);
        const label = document.getElementById(id + 'Value');
        if (slider && label) {
            slider.addEventListener('input', () => {
                label.textContent = slider.value;
            });
        }
    });

    const getFormData = () => {
        const formData = {};
        document.querySelectorAll('#inputForm select, #inputForm input').forEach(el => {
            formData[el.id] = (el.type === 'range') ? parseInt(el.value) : el.value;
        });
        
        if (customPromptInput) {
            formData['custom_prompt'] = customPromptInput.value.trim();
        }
        
        return formData;
    };

    const loadFormData = (data) => {
        for (const key in data) {
            const el = document.getElementById(key);
            if (el) {
                el.value = data[key];
                if (el.type === 'range') {
                    const label = document.getElementById(key + 'Value');
                    if (label) label.textContent = data[key];
                }
            }
        }
    };

    const fetchProfiles = async () => {
        if (!currentUser) return;
        loadProfileSelect.innerHTML = '<option value="">- Select a profile -</option>';
        const profilesRef = db.collection('users').doc(currentUser.uid).collection('student_profiles');
        try {
            const snapshot = await profilesRef.get();
            snapshot.forEach(doc => {
                const option = document.createElement('option');
                option.value = doc.id;
                option.textContent = doc.id;
                loadProfileSelect.appendChild(option);
            });
        } catch (error) {
            console.error("Error fetching profiles:", error);
        }
    };

    saveProfileBtn.addEventListener('click', async () => {
        if (!currentUser) return showToast('You must be logged in to save a profile.', 'error');
        const filename = document.getElementById('profileName').value.trim();
        if (!filename) return showToast('Please enter a profile name.', 'error');
        
        const data = getFormData();
        const profilesRef = db.collection('users').doc(currentUser.uid).collection('student_profiles');
        try {
            await profilesRef.doc(filename).set({ data: data });
            showToast('Profile saved successfully!');
            fetchProfiles();
        } catch (error) {
            console.error("Error saving profile:", error);
            showToast('Failed to save profile.', 'error');
        }
    });

    loadProfileBtn.addEventListener('click', async () => {
        if (!currentUser) return showToast('You must be logged in to load a profile.', 'error');
        const filename = loadProfileSelect.value;
        if (!filename) return showToast('Please select a profile to load.', 'error');
        
        const profileDocRef = db.collection('users').doc(currentUser.uid).collection('student_profiles').doc(filename);
        try {
            const doc = await profileDocRef.get();
            if (doc.exists) {
                loadFormData(doc.data().data);
                showToast('Profile loaded successfully!');
            } else {
                showToast('Profile not found.', 'error');
            }
        } catch (error) {
            console.error("Error loading profile:", error);
            showToast('Failed to load profile.', 'error');
        }
    });

    clearFormBtn.addEventListener('click', () => {
        const form = document.getElementById('inputForm');
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            if (input.type === 'range') {
                const defaultValue = input.defaultValue || 1;
                input.value = defaultValue;
                const label = document.getElementById(input.id + 'Value');
                if (label) label.textContent = defaultValue;
            } else if (input.tagName === 'SELECT') {
                input.selectedIndex = 0;
            } else {
                input.value = '';
            }
        });
        showToast('Form cleared.', 'info');
    });
    
    // --- Wizard Logic ---
    const updateWizardUI = () => {
        formSteps.forEach((step, index) => step.classList.toggle('active-step', index === currentStep));
        progressSteps.forEach((step, index) => step.classList.toggle('active', index < currentStep + 1));
        progressLines.forEach((line, index) => line.classList.toggle('border-indigo-600', index < currentStep));
        prevBtn.classList.toggle('hidden', currentStep === 0);
        nextBtn.classList.toggle('hidden', currentStep === formSteps.length - 1);
        generateAdviceBtn.disabled = currentStep !== formSteps.length - 1;
    };

    nextBtn.addEventListener('click', () => {
        if (currentStep < formSteps.length - 1) {
            currentStep++;
            updateWizardUI();
        }
    });

    prevBtn.addEventListener('click', () => {
        if (currentStep > 0) {
            currentStep--;
            updateWizardUI();
        }
    });

    // --- Feature Dictionary for Chart Tooltips ---
    const featureDictionary = {
        'G2': 'Second Period Grade',
        'G1': 'First Period Grade',
        'failures': 'Number of Past Failures',
        'absences': 'Number of School Absences',
        'Medu': "Mother's Education Level",
        'higher_no': 'Does Not Want Higher Education',
        'age': 'Student Age',
        'goout': 'Frequency of Going Out',
        'Fedu': "Father's Education Level",
        'Mjob_other': "Mother's Job is 'Other'",
        'schoolsup_no': 'No Extra School Support',
        'romantic_yes': 'In a Romantic Relationship'
    };
    
    const getFeatureDescription = (featureName) => {
        const cleanedName = featureName.replace('num__', '').replace('cat__', '');
        return featureDictionary[cleanedName] || cleanedName;
    };

    // --- Chart Rendering Logic ---
    const renderExplanationChart = (explanation) => {
        const ctx = document.getElementById('explanationChart').getContext('2d');
        if (explanationChart) {
            explanationChart.destroy();
        }
        const labels = explanation.map(item => item[0]);
        const dataValues = explanation.map(item => item[1]);
        const backgroundColors = dataValues.map(value => value > 0 ? 'rgba(239, 68, 68, 0.7)' : 'rgba(59, 130, 246, 0.7)');

        explanationChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels.map(getFeatureDescription),
                datasets: [{
                    label: 'Impact on Prediction',
                    data: dataValues,
                    backgroundColor: backgroundColors,
                    borderColor: backgroundColors.map(color => color.replace('0.7', '1')),
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                scales: { 
                    x: { 
                        beginAtZero: true, 
                        title: { display: true, text: 'Impact on High Risk Prediction' } 
                    } 
                },
                plugins: { 
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const originalLabel = explanation[context.dataIndex][0];
                                const description = getFeatureDescription(originalLabel);
                                let shapValue = context.raw.toFixed(4);
                                return `${description}: ${shapValue}`;
                            }
                        }
                    }
                },
                responsive: true,
                maintainAspectRatio: false
            }
        });
    };
    
    const renderShapSummary = (explanation) => {
      if (!shapSummaryDiv) return;
      
      if (!explanation || explanation.length === 0) {
        shapSummaryDiv.textContent = 'No key factors found for this prediction.';
        return;
      }
      
      const posFactors = explanation.filter(item => item[1] > 0);
      const negFactors = explanation.filter(item => item[1] < 0);
      
      let summaryText = 'This prediction was primarily influenced by:';
      
      if (posFactors.length > 0) {
        const topPos = posFactors[0];
        summaryText += ` ${getFeatureDescription(topPos[0])} which contributed to a higher risk level.`;
      }
      
      if (negFactors.length > 0) {
        const topNeg = negFactors[0];
        summaryText += ` Factors such as ${getFeatureDescription(topNeg[0])} helped to lower the risk.`;
      }
      
      shapSummaryDiv.textContent = summaryText;
    };

    const renderGradesChart = (studentData, averages) => {
      const ctx = document.getElementById('gradesChart').getContext('2d');
      if (gradesChart) {
          gradesChart.destroy();
      }
      gradesChart = new Chart(ctx, {
          type: 'bar',
          data: {
              labels: ['First Period Grade (G1)', 'Second Period Grade (G2)'],
              datasets: [{
                  label: 'Your Grades',
                  data: [studentData.G1, studentData.G2],
                  backgroundColor: 'rgba(59, 130, 246, 0.7)',
                  borderColor: 'rgba(59, 130, 246, 1)',
                  borderWidth: 1
              }, {
                  label: 'Dataset Average',
                  data: [averages.G1, averages.G2],
                  backgroundColor: 'rgba(239, 68, 68, 0.7)',
                  borderColor: 'rgba(239, 68, 68, 1)',
                  borderWidth: 1
              }]
          },
          options: {
              scales: {
                  y: {
                      beginAtZero: true,
                      max: 20
                  }
              }
          }
      });
    };

    const renderAdvice = (adviceText) => {
        const adviceOutput = document.getElementById('adviceOutput');
        adviceOutput.innerHTML = adviceText; // Assuming advice is pre-formatted HTML from API
    };

    // --- Generate Advice Event Listener (UPDATED with button loading state) ---
    generateAdviceBtn.addEventListener('click', async () => {
        const inputData = getFormData();
        
        // --- MODIFIED: Button-specific loading state ---
        const originalBtnText = generateAdviceBtn.innerHTML;
        generateAdviceBtn.innerHTML = `<span class="button-loader"></span>Generating...`;
        generateAdviceBtn.disabled = true;
        
        resultsSection.classList.remove('hidden');
        loadingSpinner.classList.add('hidden'); // Hide the main spinner
        
        // Clear previous content
        document.getElementById('adviceOutput').innerHTML = '';
        document.getElementById('riskLevel').textContent = 'Calculating...';
        const chartContainer = document.getElementById('explanationChartContainer');
        chartContainer.innerHTML = '<canvas id="explanationChart"></canvas>';
        const gradesChartContainer = document.getElementById('gradesChartContainer');
        gradesChartContainer.innerHTML = '<canvas id="gradesChart"></canvas>';
        if (shapSummaryDiv) shapSummaryDiv.textContent = '';


        try {
            const [riskResponse, adviceResponse, explanationResponse, gradesResponse] = await Promise.all([
                fetch('/predict-risk', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ student_data: inputData }) }),
                fetch('/generate-advice', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ student_data: inputData }) }),
                fetch('/explain-prediction', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ student_data: inputData }) }),
                fetch('/get-grade-averages')
            ]);

            if (!riskResponse.ok) throw new Error(`Risk prediction failed: ${riskResponse.statusText}`);
            const riskResult = await riskResponse.json();
            const riskLevel = riskResult.risk_level;
            document.getElementById('riskLevel').textContent = riskLevel;
            const riskColor = riskLevel === 'High' ? 'text-red-500' : (riskLevel === 'Medium' ? 'text-yellow-500' : 'text-green-500');
            document.getElementById('riskLevel').className = `font-bold ${riskColor}`;

            if (!adviceResponse.ok) throw new Error(`Advice generation failed: ${adviceResponse.statusText}`);
            const adviceResult = await adviceResponse.json();
            renderAdvice(adviceResult.advice);

            if (!explanationResponse.ok) throw new Error(`Explanation generation failed: ${explanationResponse.statusText}`);
            const explanationResult = await explanationResponse.json();
            if (explanationResult.explanation) {
                renderExplanationChart(explanationResult.explanation);
                renderShapSummary(explanationResult.explanation);
            }
            
            if (!gradesResponse.ok) throw new Error(`Grade averages fetch failed: ${gradesResponse.statusText}`);
            const gradesAverages = await gradesResponse.json();
            renderGradesChart(inputData, gradesAverages);

        } catch (error) {
            console.error("Error during generation process:", error);
            document.getElementById('adviceOutput').innerHTML = `<p class="text-red-500">Failed to generate advice: ${error.message}</p>`;
        } finally {
            // --- MODIFIED: Restore button state ---
            generateAdviceBtn.innerHTML = originalBtnText;
            generateAdviceBtn.disabled = false;
        }
    });

    copyAdviceBtn.addEventListener('click', () => {
        const adviceContent = document.getElementById('adviceOutput').innerText;
        navigator.clipboard.writeText(adviceContent).then(() => {
            showToast('Advice copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            showToast('Failed to copy advice.', 'error');
        });
    });

    updateWizardUI(); 
}

document.addEventListener('DOMContentLoaded', initializeFirebase);