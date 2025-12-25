# 🎓 AI Student Mentor — Student Risk Demo

Flask web app that predicts student academic risk, explains key factors with SHAP, and generates mentoring advice using Google Gemini.

Live app: https://student-risk-demo.onrender.com

> Note: Free Render services can pause on inactivity, causing a ~50s cold-start delay on the first request.

---

## ✨ Features
- Risk classification (High/Medium/Low) and final grade estimate.
- SHAP-based key factor explanations per prediction.
- AI mentoring advice via Google Gemini.
- Authentication + dashboard, history, assessment flow.

---

## 🚀 Quick Start (Local)

### Prerequisites
- Python 3.12+
- Gemini API key (create via Google AI Studio)
- Firebase project credentials

### Setup
```bash
git clone <your-repo-url>
cd student-risk-demo

python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate # macOS/Linux

pip install -r requirements.txt
```

### Generate Models (required)
```bash
python train_model.py
```
This creates the joblib files used in production:
- early_warning_model_pipeline_tuned.joblib
- student_risk_classifier_tuned.joblib
- label_encoder.joblib

### Environment variables
Create a `.env` next to the app files:
```env
# Gemini
GEMINI_API_KEY=your_gemini_key

# Firebase
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id

# Optional (email alerts for high risk)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
```

### Run locally
```bash
python run.py
```
App runs at http://127.0.0.1:8501

---

## 🔌 API Endpoints

- `GET /healthz` — lightweight health check.
- `GET /status` — which models are loaded.
- `POST /api/predict` — returns prediction, risk category, confidence, SHAP values, and mentoring advice.

Example request:
```bash
curl -X POST http://127.0.0.1:8501/api/predict \
	-H "Content-Type: application/json" \
	-d "{\"school\":\"GP\",\"sex\":\"F\",\"age\":17,\"address\":\"U\",\"famsize\":\"GT3\",\"Pstatus\":\"A\",\"Medu\":3,\"Fedu\":2,\"Mjob\":\"teacher\",\"Fjob\":\"services\",\"reason\":\"course\",\"guardian\":\"mother\",\"traveltime\":1,\"studytime\":2,\"failures\":0,\"schoolsup\":\"no\",\"famsup\":\"yes\",\"paid\":\"no\",\"activities\":\"yes\",\"nursery\":\"yes\",\"higher\":\"yes\",\"internet\":\"yes\",\"romantic\":\"no\",\"famrel\":4,\"freetime\":3,\"goout\":3,\"Dalc\":1,\"Walc\":1,\"health\":4,\"absences\":4,\"G1\":8,\"G2\":8,\"average_grade\":8.0,\"grade_change\":0.0}"
```

---

## ☁️ Deploy to Render

The repo already contains a Procfile:
- [Procfile](Procfile): `web: gunicorn run:app --bind 0.0.0.0:$PORT`

Steps
1. Create a new Web Service (Python) and connect your repo.
2. Ensure `requirements.txt` includes `gunicorn` and `Flask` (already present).
3. Set environment variables shown above (Render → Environment).
4. First request after inactivity may be slow due to cold start.

Health checks
- Use `GET https://student-risk-demo.onrender.com/healthz` to verify service quickly.

---

## 📁 Project Structure

```text
student-risk-demo/
├── app/
│   ├── static/
│   ├── templates/
│   ├── views/
│   ├── limits.py
│   ├── routes.py
│   └── __init__.py
├── docs/
├── logs/
├── run.py
├── train_model.py
├── requirements.txt
├── Procfile
├── early_warning_model_pipeline_tuned.joblib
├── student_risk_classifier_tuned.joblib
├── label_encoder.joblib
└── README.md
```

---

## 🧪 Model & Explainability
- LightGBM/XGBoost based classifiers.
- SHAP explanations for top contributing features.

---

## 🛠️ Troubleshooting
- Startup error about missing env vars: ensure all critical variables in `.env` are set.
- 500 “Models not loaded”: run `python train_model.py` and confirm `.joblib` files exist at project root.
- Slow initial response on Render: expected for free tier; hit `/healthz` or consider upgrading.

---

Built with Flask, scikit-learn, LightGBM, SHAP, Firebase, and Google Gemini.