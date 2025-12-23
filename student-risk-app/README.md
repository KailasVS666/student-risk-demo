# 🎓 AI Student Mentor - Risk Prediction System

A Flask-based web application that predicts student academic risk levels using machine learning and provides personalized AI-powered mentoring advice via Google's Gemini API.

## ✨ Features

- **Risk Classification**: Predicts whether a student is at Low, Medium, or High academic risk
- **AI Mentoring Advice**: Generates personalized guidance using Google Gemini 2.5 Flash
- **SHAP Explanations**: Shows which factors most influence each prediction
- **Student Profiles**: Save and load student data via Firebase Firestore
- **Interactive UI**: Multi-step wizard form with real-time visualizations
- **Firebase Authentication**: Secure user login and profile management

---

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.8 or higher
- Git
- A Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Firebase project credentials ([Create project](https://console.firebase.google.com/))

### 1. Clone the Repository

```bash
git clone https://github.com/KailasVS666/student-risk-demo.git
cd student-risk-demo/student-risk-app
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate ML Models

⚠️ **CRITICAL STEP**: Model files are not included in the repository due to their size. You must generate them locally:

```bash
python train_model.py
```

This will create three files:
- `early_warning_model_pipeline_tuned.joblib` - Full ML pipeline
- `student_risk_classifier_tuned.joblib` - Core LightGBM classifier
- `label_encoder.joblib` - Categorical feature encoders

**Expected Output:**
```
Training the student risk classification model...
Training complete.
--- Model Evaluation ---
              precision    recall  f1-score   support
        High       0.XX      0.XX      0.XX       XX
         Low       0.XX      0.XX      0.XX       XX
      Medium       0.XX      0.XX      0.XX       XX
...
```

### 5. Configure Environment Variables

Create a `.env` file in the `student-risk-app/` directory:

```env
# ========================================
# Google Gemini AI Configuration
# ========================================
GEMINI_API_KEY=your_gemini_api_key_here

# ========================================
# Firebase Configuration
# ========================================
# Get these from Firebase Console > Project Settings > General
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789012
FIREBASE_APP_ID=1:123456789012:web:abcdef123456
FIREBASE_MEASUREMENT_ID=G-ABCDEFG123
```

**How to Get Firebase Credentials:**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project (or select existing)
3. Click the gear icon ⚙️ → **Project settings**
4. Scroll down to "Your apps" → **Web app** → Copy config values
5. Enable **Authentication** (Email/Password) and **Firestore Database**

### 6. Run the Application

```bash
python run.py
```

The app will start on **http://localhost:8501**

---

## 📁 Project Structure

```
student-risk-app/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── routes.py             # API endpoints & prediction logic
│   ├── static/
│   │   ├── script.js         # Frontend JavaScript
│   │   └── style.css         # Custom styles
│   └── templates/
│       └── index.html        # Main UI
├── student-mat.csv           # Math course dataset
├── student-por.csv           # Portuguese course dataset
├── train_model.py            # Model training script
├── run.py                    # Application entry point
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── .gitignore                # Git exclusions
└── README.md                 # This file
```

---

## 🛠️ Usage Guide

### First Time Setup

1. **Create an Account**: Click "Sign Up" on the login page
2. **Fill Student Profile**: Complete the 3-step wizard form
3. **Generate Analysis**: Click "Generate Mentoring Advice"
4. **View Results**: See risk prediction, SHAP explanations, and AI advice

### Saving Profiles

1. Enter a profile name (e.g., "john_doe_2024")
2. Click "Save Profile"
3. Profile is saved to your Firebase account

### Loading Profiles

1. Select a saved profile from the dropdown
2. Click "Load Profile"
3. Form auto-fills with saved data

### Custom Advice Requests

Use the "Custom Advice Request" text box to ask for specific guidance:
- *"Focus on strategies for improving math grades"*
- *"Suggest time management techniques for students with part-time jobs"*
- *"Address anxiety and test preparation strategies"*

---

## 🔧 Troubleshooting

### Error: "Missing required environment variables"

**Solution**: Ensure your `.env` file exists and contains all required variables. Check for typos.

```bash
# Verify .env file exists
ls -la .env  # Mac/Linux
dir .env     # Windows
```

### Error: "Model files not found"

**Solution**: Run the training script to generate model files:

```bash
python train_model.py
```

### Error: "Firebase permission denied"

**Solution**: Configure Firestore security rules:

1. Go to Firebase Console → Firestore Database → Rules
2. Use these rules for development:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /profiles/{userId}/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

### SHAP Errors

If you see SHAP-related errors, ensure `shap` is installed:

```bash
pip install shap==0.48.0
```

### Port Already in Use

If port 8501 is busy, change it in `run.py`:

```python
app.run(debug=True, port=8502)  # Use different port
```

---

## 🧪 Model Information

### Algorithm
- **LightGBM Classifier** with balanced class weights
- **3-class prediction**: High Risk, Medium Risk, Low Risk

### Features Used (33 total)
- **Demographics**: Age, sex, school, address, family size
- **Academic**: Study time, failures, past grades (G1, G2)
- **Family**: Parent education, jobs, family support
- **Lifestyle**: Free time, going out, health, absences
- **Engineered**: Average grade, grade change (G2 - G1)

### Risk Thresholds
- **High Risk**: Final grade (G3) < 10 out of 20
- **Medium Risk**: Final grade 10-13
- **Low Risk**: Final grade > 13

### Model Performance
- F1-Score: ~0.75-0.85 (varies by class)
- Uses SHAP TreeExplainer for feature importance

---

## 🔒 Security Notes

- ✅ All secrets stored in `.env` file (excluded from git)
- ✅ Environment variable validation on startup
- ✅ Firebase authentication required for profile access
- ✅ Server-side input validation (see routes.py)
- ⚠️ **NEVER commit `.env` file to version control**

---

## 📊 Dataset Attribution

This project uses the **Student Performance Dataset** from:

> P. Cortez and A. Silva. Using Data Mining to Predict Secondary School Student Performance.  
> In A. Brito and J. Teixeira (Eds.), *Proceedings of 5th FUture BUsiness TEChnology Conference (FUBUTEC 2008)*,  
> pp. 5-12, Porto, Portugal, April 2008.

**Citation:**
```bibtex
@inproceedings{cortez2008data,
  title={Using data mining to predict secondary school student performance},
  author={Cortez, Paulo and Silva, Alice Maria Gon{\c{c}}alves},
  booktitle={Proceedings of 5th Annual Future Business Technology Conference},
  pages={5--12},
  year={2008}
}
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is for educational purposes. Please ensure compliance with dataset licensing and API terms of service.

---

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/KailasVS666/student-risk-demo/issues)
- **Email**: [Your contact email]
- **Documentation**: This README

---

## 🎯 Roadmap

- [ ] Add Docker containerization
- [ ] Implement rate limiting on API endpoints
- [ ] Add unit tests (pytest)
- [ ] Support for multiple languages
- [ ] Export reports as PDF
- [ ] Batch prediction upload (CSV)
- [ ] Model retraining interface

---

**Built with ❤️ using Flask, LightGBM, Firebase, and Google Gemini AI**
