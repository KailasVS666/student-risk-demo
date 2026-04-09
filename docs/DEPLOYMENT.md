# Deployment Guide

## Local Development

### Prerequisites
- Python 3.11 or newer
- Node.js for Tailwind builds
- Firebase project with Auth and Firestore
- Gemini API key

### Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
npm install
```

### Environment Variables
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_key
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
FIREBASE_MEASUREMENT_ID=optional_measurement_id
SECRET_KEY=your_secret_key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
```

### Run Locally
```bash
python train_model.py
npm run tailwind:build
python run.py
```

The app runs on `http://127.0.0.1:8501`.

## Render Deployment

This repository is configured for Render with `render.yaml`, `build.sh`, and `Procfile`.

### Build Flow
`build.sh` does the following:
1. Installs Python dependencies.
2. Runs `npm install`.
3. Trains the model if the `.joblib` artifacts are missing.
4. Builds the Tailwind CSS bundle.

### Render Settings
- Build command: `bash build.sh`
- Start command: `gunicorn run:app --bind 0.0.0.0:$PORT`
- Environment: `ENVIRONMENT=production`

### Required Render Env Vars
- `GEMINI_API_KEY`
- `FIREBASE_API_KEY`
- `FIREBASE_AUTH_DOMAIN`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_STORAGE_BUCKET`
- `FIREBASE_MESSAGING_SENDER_ID`
- `FIREBASE_APP_ID`
- `SECRET_KEY`

Optional:
- `FIREBASE_MEASUREMENT_ID`
- `MAIL_SERVER`
- `MAIL_PORT`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`

### Notes
- First deploy may take a few minutes because the ML model can be trained during the build.
- If the model files already exist, the build skips training.
- Cold starts are expected on the free tier.

## Verification
After deploy, check:
- `GET /healthz`
- `GET /status`
- `POST /api/predict`

If prediction fails, confirm the model artifacts exist at the project root:
- `early_warning_model_pipeline_tuned.joblib`
- `student_risk_classifier_tuned.joblib`
- `label_encoder.joblib`