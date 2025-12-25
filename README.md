Here is the polished, high-impact `README.md` for your repository. It incorporates the final directory structure we verified and follows your preferred formatting style.

---

# 🎓 AI Student Mentor - Risk Prediction System

A professional Flask-based web application that predicts student academic risk levels using **LightGBM** and provides personalized AI-powered mentoring advice via the **Google Gemini 1.5 Flash API**.

## ✨ Features

* **Risk Classification**: Predicts whether a student is at Low, Medium, or High academic risk.
* **AI Mentoring Advice**: Generates personalized, context-aware guidance using **Gemini 1.5 Flash**.
* **SHAP Explanations**: Visualizes the specific factors (features) influencing each prediction.
* **Student Profiles**: Securely save and load student data via **Firebase Firestore**.
* **Interactive UI**: A modern, multi-step wizard form with real-time feedback.
* **Firebase Authentication**: Robust user login and profile management.

---

## 🚀 Quick Start Guide

### Prerequisites

* Python 3.12+
* Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))
* Firebase Project Credentials ([Create project](https://console.firebase.google.com/))

### 1. Clone the Repository

```bash
git clone https://github.com/KailasVS666/student-risk-demo.git
cd student-risk-demo/student-risk-app

```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

### 4. Generate ML Models

⚠️ **CRITICAL**: You must generate the model binaries locally before running the app:

```bash
python train_model.py

```

### 5. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Firebase Configuration
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id

```

### 6. Run the Application

```bash
python run.py

```

The app will start on **[http://127.0.0.1:8501](http://127.0.0.1:8501)**

---

## 📁 Project Structure

```text
student-risk-app/
├── app/
│   ├── static/             # CSS and JavaScript assets
│   ├── templates/          # HTML Jinja2 templates
│   ├── views/              # Modular route blueprints
│   ├── limits.py           # Rate limiting logic
│   ├── routes.py           # Core API & Prediction logic
│   └── __init__.py         # App factory & initialization
├── docs/                   # User and Deployment guides
├── logs/                   # Application runtime logs
├── student-mat.csv         # Math dataset
├── student-por.csv         # Portuguese dataset
├── train_model.py          # Model training script
├── run.py                  # Entry point
└── requirements.txt        # Dependencies

```

---

## 🛠️ Usage Guide

* **Create an Account**: Sign up to start managing student profiles.
* **Fill Student Profile**: Complete the assessment wizard with student demographics and grades.
* **Generate Analysis**: View the risk level and the **AI Mentor** insights.
* **Custom Requests**: Use the "Custom Advice Request" box to ask Gemini specific questions like *"Focus on time management for math."*

---

## 🧪 Model Information

* **Algorithm**: LightGBM Classifier with balanced class weights.
* **Classes**: High Risk (G3 < 10), Medium Risk (G3 10-13), Low Risk (G3 > 13).
* **Features**: 33 variables including G1/G2 grades, absences, study time, and family background.
* **Explainability**: Integrated with **SHAP** for local feature importance per student.

---

## 🔒 Security Notes

* ✅ Secrets are stored in `.env` (excluded from Git via `.gitignore`).
* ✅ Firebase security rules ensure users can only access their own profiles.
* ✅ Server-side input validation on all prediction endpoints.

---

## 📊 Dataset Attribution

This project utilizes the **Student Performance Dataset** from the UCI Machine Learning Repository.

> P. Cortez and A. Silva. Using Data Mining to Predict Secondary School Student Performance. In A. Brito and J. Teixeira (Eds.), Proceedings of 5th FUture BUsiness TEChnology Conference (FUBUTEC 2008).

---

**Built with ❤️ using Flask, LightGBM, Firebase, and Google Gemini AI**