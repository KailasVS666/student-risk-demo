# AI Student Mentor

Flask app for student academic risk assessment. It predicts risk level, estimates a final grade band, explains the result, and generates mentoring advice with Gemini.

Live app: https://student-risk-demo.onrender.com

## What’s Included
- Multi-step assessment form for student profile data.
- Risk prediction with a trained LightGBM pipeline.
- Fallback feature-importance explanations for the result.
- Personalized mentoring advice using Google Gemini.
- Firebase-backed authentication, dashboard, and history views.
- PDF export and email alert support for high-risk cases.

## Machine Learning
The prediction model is trained in [train_model.py](train_model.py) on the UCI student performance datasets (`student-mat.csv` and `student-por.csv`). The target is derived from final grade `G3`, mapped into three classes: `High`, `Medium`, and `Low` risk.

The training pipeline does three main things:
- combines both datasets into one training set
- engineers `average_grade` and `grade_change` as extra signals
- trains a LightGBM classifier with preprocessing, imputation, scaling, and grid search

At inference time, the app loads the saved artifacts:
- `early_warning_model_pipeline_tuned.joblib` for the full prediction pipeline
- `label_encoder.joblib` for categorical encoding
- `student_risk_classifier_tuned.joblib` for the classifier used in the explanation flow

The API converts the student form into the model schema, predicts the risk class, and derives a final-grade estimate from the predicted class confidence. The app also returns feature-importance summaries and uses Gemini to generate mentoring advice.

Important note: the current runtime explanation path uses a fallback feature-importance list when full SHAP calculation is not practical in the deployment environment, so the explanation is informative but not a full SHAP computation at request time.

## Project Docs
- [User Guide](docs/USER_GUIDE.md)
- [API Reference](docs/API_DOCS.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Test Suite README](tests/README.md)

## Quick Start
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python train_model.py
python run.py
```

## Required Environment Variables
Set these in `.env` before running the app:
- `GEMINI_API_KEY`
- `FIREBASE_API_KEY`
- `FIREBASE_AUTH_DOMAIN`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_STORAGE_BUCKET`
- `FIREBASE_MESSAGING_SENDER_ID`
- `FIREBASE_APP_ID`
- `SECRET_KEY`

Optional email alert settings:
- `MAIL_SERVER`
- `MAIL_PORT`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`

## Model Artifacts
The app expects these files at the project root:
- `early_warning_model_pipeline_tuned.joblib`
- `student_risk_classifier_tuned.joblib`
- `label_encoder.joblib`

If they are missing, run `python train_model.py` or let the Render build script generate them.

## Tech Stack
Flask, scikit-learn, LightGBM, SHAP-inspired feature summaries, Firebase, Google Gemini, Tailwind CSS, Chart.js.