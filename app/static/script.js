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
        
        // Add custom prompt to form data
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
        if (!currentUser) return alert('You must be logged in to save a profile.');
        const filename = document.getElementById('profileName').value.trim();
        if (!filename) return alert('Please enter a filename.');
        
        const data = getFormData();
        const profilesRef = db.collection('users').doc(currentUser.uid).collection('student_profiles');
        try {
            await profilesRef.doc(filename).set({ data: data });
            alert('Profile saved successfully!');
            fetchProfiles();
        } catch (error) {
            console.error("Error saving profile:", error);
            alert('Failed to save profile.');
        }
    });

    loadProfileBtn.addEventListener('click', async () => {
        if (!currentUser) return alert('You must be logged in to load a profile.');
        const filename = loadProfileSelect.value;
        if (!filename) return alert('Please select a profile to load.');
        
        const profileDocRef = db.collection('users').doc(currentUser.uid).collection('student_profiles').doc(filename);
        try {
            const doc = await profileDocRef.get();
            if (doc.exists) {
                loadFormData(doc.data().data);
                alert('Profile loaded successfully!');
            } else {
                alert('Profile not found.');
            }
        } catch (error) {
            console.error("Error loading profile:", error);
            alert('Failed to load profile.');
        }
    });

    clearFormBtn.addEventListener('click', () => {
        const form = document.getElementById('inputForm');
        const inputs = form.querySelectorAll('input, select');
        
        inputs.forEach(input => {
            const defaultValue = input.getAttribute('value') || input.querySelector('option').value;
            input.value = defaultValue;
            
            // Update the display for range sliders
            if (input.type === 'range') {
                const label = document.getElementById(input.id + 'Value');
                if (label) {
                    label.textContent = defaultValue;
                }
            }
        });
        if (customPromptInput) {
            customPromptInput.value = '';
        }
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

    // --- NEW: Feature Dictionary for Chart Tooltips ---
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


    // --- Chart Rendering Logic (UPDATED with tooltips) ---
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
    
    // --- NEW: Function to render a dynamic SHAP summary
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

    // --- Function to render advice with interactive checklist ---
    const renderAdvice = (adviceText) => {
        const adviceOutput = document.getElementById('adviceOutput');
        let html = '';
        
        // Split advice into sections
        const sections = adviceText.split('### ');
        
        sections.forEach(section => {
            if (!section.trim()) return;

            const lines = section.split('\n');
            const title = lines.shift().trim();
            let content = lines.join('<br>').trim();

            html += `<h3>${title}</h3>`;

            // Special handling for Actionable Steps to create a checklist
            if (title.includes("Actionable Steps")) {
                const steps = content.split('<br>').filter(line => line.trim().startsWith('* '));
                html += '<ul class="checklist">';
                steps.forEach((step, index) => {
                    const stepText = step.replace('* ', '').trim();
                    if(stepText) {
                        html += `<li>
                                    <input type="checkbox" id="step-${index}" />
                                    <label for="step-${index}">${stepText}</label>
                                 </li>`;
                    }
                });
                html += '</ul>';
            } else {
                html += `<p>${content.replace(/\* /g, '<br>&bull; ')}</p>`;
            }
        });
        
        // This is the correct way to add the adviceContent div
        const contentDiv = document.createElement('div');
        contentDiv.id = 'adviceContent';
        contentDiv.innerHTML = html;
        
        adviceOutput.innerHTML = '';
        adviceOutput.appendChild(contentDiv);
    };

    // --- Generate Advice Event Listener ---
    generateAdviceBtn.addEventListener('click', async () => {
        const inputData = getFormData();
        
        // Show loading state and disable button
        resultsSection.classList.remove('hidden');
        loadingSpinner.classList.remove('hidden');
        generateAdviceBtn.disabled = true;
        
        // Clear previous content
        document.getElementById('adviceOutput').innerHTML = '';
        document.getElementById('riskLevel').textContent = 'Calculating...';
        const chartContainer = document.getElementById('explanationChartContainer');
        chartContainer.innerHTML = '<canvas id="explanationChart"></canvas>';
        if (shapSummaryDiv) shapSummaryDiv.textContent = '';


        try {
            const [riskResponse, adviceResponse, explanationResponse] = await Promise.all([
                fetch('/predict-risk', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ student_data: inputData }) }),
                fetch('/generate-advice', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ student_data: inputData }) }),
                fetch('/explain-prediction', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ student_data: inputData }) })
            ]);

            // Process Risk
            if (!riskResponse.ok) throw new Error(`Risk prediction failed with status: ${riskResponse.status}`);
            const riskResult = await riskResponse.json();
            const riskLevel = riskResult.risk_level;
            document.getElementById('riskLevel').textContent = riskLevel;
            const riskColor = riskLevel === 'High' ? 'text-red-500' : (riskLevel === 'Medium' ? 'text-yellow-500' : 'text-green-500');
            document.getElementById('riskLevel').className = `font-bold ${riskColor}`;

            // Process and Render Advice
            if (!adviceResponse.ok) throw new Error(`Advice generation failed with status: ${adviceResponse.status}`);
            const adviceResult = await adviceResponse.json();
            renderAdvice(adviceResult.advice);

            // Process and Render Chart
            if (!explanationResponse.ok) throw new Error(`Explanation failed with status: ${explanationResponse.status}`);
            const explanationResult = await explanationResponse.json();
            if (explanationResult.explanation) {
                renderExplanationChart(explanationResult.explanation);
                renderShapSummary(explanationResult.explanation);
            }

        } catch (error) {
            console.error("Error during generation process:", error);
            document.getElementById('adviceOutput').innerHTML = `<p class="text-red-500">Failed to generate advice: ${error.message}</p>`;
        } finally {
            // Hide loading state and re-enable button
            loadingSpinner.classList.add('hidden');
            generateAdviceBtn.disabled = false;
        }
    });

    // --- Copy to Clipboard Logic ---
    copyAdviceBtn.addEventListener('click', () => {
        const adviceContent = document.getElementById('adviceContent');
        if (adviceContent) {
            navigator.clipboard.writeText(adviceContent.innerText).then(() => {
                const originalText = copyAdviceBtn.innerHTML;
                copyAdviceBtn.textContent = 'Copied!';
                setTimeout(() => {
                    copyAdviceBtn.innerHTML = originalText;
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
            });
        }
    });

    // --- Initialize the wizard ---
    updateWizardUI(); 
}

document.addEventListener('DOMContentLoaded', initializeFirebase);