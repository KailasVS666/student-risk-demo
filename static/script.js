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
    const authContainer = document.getElementById('auth-container');
    const appContainer = document.getElementById('app');
    const authError = document.getElementById('auth-error');

    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const loginBtn = document.getElementById('loginBtn');
    const signupBtn = document.getElementById('signupBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const userEmailSpan = document.getElementById('user-email');

    const inputForm = document.getElementById('inputForm');
    const resultsSection = document.getElementById('resultsSection');
    const generateAdviceBtn = document.getElementById('generateAdviceBtn');
    const saveProfileBtn = document.getElementById('saveProfileBtn');
    const loadProfileBtn = document.getElementById('loadProfileBtn');
    const loadProfileSelect = document.getElementById('loadProfileSelect');

    let currentUser = null;

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

    generateAdviceBtn.addEventListener('click', async () => {
        const inputData = getFormData();
        resultsSection.classList.remove('hidden');
        document.getElementById('adviceOutput').innerHTML = '<p class="text-center text-gray-500">Generating advice...</p>';
        document.getElementById('riskLevel').textContent = 'Calculating...';

        try {
            const riskResponse = await fetch('/predict-risk', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ student_data: inputData })
            });

            if (!riskResponse.ok) {
                throw new Error(`Risk prediction failed with status: ${riskResponse.status}`);
            }
            
            const riskResult = await riskResponse.json();
            const riskLevel = riskResult.risk_level;

            document.getElementById('riskLevel').textContent = riskLevel;
            document.getElementById('riskLevel').className = `font-bold ${riskLevel === 'High' ? 'text-red-500' : 'text-green-500'}`;
            
            const adviceResponse = await fetch('/generate-advice', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ student_data: inputData })
            });

            if (!adviceResponse.ok) {
                throw new Error(`Server call failed with status: ${adviceResponse.status}`);
            }

            const result = await adviceResponse.json();
            
            let htmlAdvice = result.advice.replace(/### (.*)/g, '<h3>$1</h3>').replace(/\n/g, '<br>');
            document.getElementById('adviceOutput').innerHTML = htmlAdvice;

        } catch (error) {
            console.error("Error during generation process:", error);
            document.getElementById('adviceOutput').innerHTML = `<p class="text-red-500">Failed to generate advice: ${error.message}</p>`;
        }
    });
}

document.addEventListener('DOMContentLoaded', initializeFirebase);