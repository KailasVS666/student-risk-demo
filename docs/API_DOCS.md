# API Reference

## Base URL
- Local: `http://127.0.0.1:8501`
- Production: your deployed Render URL

All endpoints accept and return JSON unless noted otherwise.

## Authentication
The browser app uses Firebase Auth. JSON endpoints are protected by input validation and rate limiting.

## Endpoints

### `GET /`
Redirects to `/login`.

### `GET /healthz`
Lightweight health check.

Example response:
```json
{
  "ok": true,
  "models_loaded": true,
  "time": "2026-04-09T12:00:00Z"
}
```

### `GET /status`
Returns model loading status.

Example response:
```json
{
  "pipeline": true,
  "label_encoder": true,
  "risk_explainer": true
}
```

### `POST /api/predict`
Predicts student risk, estimated final grade, explanation factors, and mentoring advice.

Rate limit: `30 per minute`

Request body example:
```json
{
  "school": "GP",
  "sex": "F",
  "age": 17,
  "address": "U",
  "famsize": "GT3",
  "Pstatus": "A",
  "Medu": 3,
  "Fedu": 2,
  "Mjob": "teacher",
  "Fjob": "services",
  "reason": "course",
  "guardian": "mother",
  "traveltime": 1,
  "studytime": 2,
  "failures": 0,
  "schoolsup": "no",
  "famsup": "yes",
  "paid": "no",
  "activities": "yes",
  "nursery": "yes",
  "higher": "yes",
  "internet": "yes",
  "romantic": "no",
  "famrel": 4,
  "freetime": 3,
  "goout": 3,
  "Dalc": 1,
  "Walc": 1,
  "health": 4,
  "absences": 4,
  "G1": 8,
  "G2": 8,
  "customPrompt": "Focus on study habits and time management"
}
```

Response example:
```json
{
  "prediction": 10,
  "risk_category": "high",
  "risk_descriptor": "Requires immediate intervention and support.",
  "confidence": 0.83,
  "probabilities": {
    "High": 0.83,
    "Low": 0.06,
    "Medium": 0.11
  },
  "shap_values": [
    {"feature": "G2 Grade", "importance": 0.85},
    {"feature": "Failures", "importance": 0.65}
  ],
  "mentoring_advice": "...",
  "status": "success"
}
```

Common errors:
- `400` for validation failures
- `503` when model artifacts are unavailable
- `429` when rate limits are exceeded

### `POST /generate-pdf`
Generates a PDF report from assessment results.

Rate limit: `5 per minute`

Required fields:
- `predicted_grade`
- `risk_category`
- `confidence`

Optional fields:
- `risk_descriptor`
- `mentoring_advice`
- `shap_values`

Returns an `application/pdf` download on success.

## Page Routes
- `GET /login`
- `GET /signup`
- `GET /logout`
- `GET /dashboard`
- `GET /assessment`
- `GET /results`
- `GET /history`
- `GET /settings`
- `GET /about`
- `GET /landing`

## Student Feature Schema
Prediction input uses the student-performance feature set:
- Demographics: `school`, `sex`, `age`, `address`, `famsize`, `Pstatus`
- Family context: `Medu`, `Fedu`, `Mjob`, `Fjob`, `guardian`, `famrel`
- Academic context: `reason`, `schoolsup`, `famsup`, `paid`, `higher`, `studytime`, `traveltime`, `failures`
- Lifestyle: `activities`, `nursery`, `internet`, `romantic`, `freetime`, `goout`, `Dalc`, `Walc`, `health`, `absences`
- Grades: `G1`, `G2`
- Derived fields: `average_grade`, `grade_change`

## Notes
- `customPrompt` is optional and only adjusts the advice prompt.
- In low-resource environments, the app returns fallback feature importance instead of computing full SHAP values.