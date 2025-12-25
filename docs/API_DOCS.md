# API Documentation - AI Student Mentor

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
4. [Request/Response Formats](#requestresponse-formats)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Examples](#examples)

---

## Overview

The AI Student Mentor API provides endpoints for student risk assessment and prediction. The API is built with Flask and uses Firebase for authentication and data storage.

### Base URL
```
http://localhost:8501 (Development)
https://your-domain.com (Production)
```

### API Version
Current Version: `v1`

### Content Type
All requests and responses use `application/json` content type.

---

## Authentication

### Firebase Authentication
The application uses **Firebase Auth** for user authentication. All API endpoints (except public routes) require a valid Firebase ID token.

#### Client-Side Authentication
```javascript
firebase.auth().onAuthStateChanged(user => {
    if (user) {
        // User is signed in
        const idToken = await user.getIdToken();
        // Include token in API requests
    }
});
```

#### Protected Routes
Most page routes require authentication. If not authenticated, users are redirected to `/login`.

---

## Endpoints

### 1. Root Endpoint
**GET** `/`

Redirects to `/login` page.

**Response:**
- `302 Redirect` to `/login`

---

### 2. Prediction Endpoint
**POST** `/api/predict`

Generates risk prediction and mentoring advice for a student profile.

**Rate Limit:** 30 requests/minute per IP

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "school": "GP",
    "sex": "F",
    "age": 17,
    "address": "U",
    "famsize": "GT3",
    "Pstatus": "T",
    "Medu": 3,
    "Fedu": 2,
    "Mjob": "services",
    "Fjob": "other",
    "reason": "course",
    "guardian": "mother",
    "traveltime": 2,
    "studytime": 2,
    "failures": 0,
    "schoolsup": "yes",
    "famsup": "yes",
    "paid": "no",
    "activities": "yes",
    "nursery": "yes",
    "higher": "yes",
    "internet": "yes",
    "romantic": "no",
    "famrel": 4,
    "freetime": 3,
    "goout": 2,
    "Dalc": 1,
    "Walc": 1,
    "health": 3,
    "absences": 5,
    "G1": 14,
    "G2": 15,
    "custom_prompt": "Focus on study habits and time management"
}
```

**Response (Success):**
```json
{
    "prediction": "Low",
    "probabilities": {
        "High": 0.12,
        "Low": 0.68,
        "Medium": 0.20
    },
    "confidence": "68.2%",
    "confidence_value": 0.682,
    "shap_chart_url": "data:image/png;base64,...",
    "shap_values": {
        "G2": 0.45,
        "G1": 0.38,
        "failures": -0.22,
        ...
    },
    "shap_summary": "The top factors influencing this prediction are: G2 (15) increased risk by +0.45...",
    "mentoring_advice": "<h2>📚 Academic Performance Analysis</h2><p>Based on the grades...</p>",
    "grades": {
        "G1": 14,
        "G2": 15
    }
}
```

**Response (Error):**
```json
{
    "error": "Missing required field: age"
}
```

**Status Codes:**
- `200 OK`: Successful prediction
- `400 Bad Request`: Missing or invalid input data
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server processing error

---

### 3. Authentication Routes

#### Login Page
**GET** `/login`

Returns the login page HTML.

#### Signup Page
**GET** `/signup`

Returns the signup page HTML.

#### Logout
**GET** `/logout`

Logs out the user (client-side Firebase logout).

---

### 4. Dashboard Routes

#### Dashboard
**GET** `/dashboard`

Returns the user dashboard with stats and recent profiles.

**Authentication Required:** Yes

**Response:** HTML page with Firebase config injected

---

#### Assessment Form
**GET** `/assessment`

Returns the student assessment form.

**Authentication Required:** Yes

**Response:** HTML page with assessment form

---

#### Results Page
**GET** `/results`

Returns the results display page.

**Authentication Required:** Yes

**Response:** HTML page showing risk analysis

---

#### History Page
**GET** `/history`

Returns the assessment history page with search and filters.

**Authentication Required:** Yes

**Response:** HTML page with profile history

---

#### Settings Page
**GET** `/settings`

Returns the user settings and preferences page.

**Authentication Required:** Yes

**Response:** HTML page with account settings

---

#### About Page
**GET** `/about`

Returns the about/info page.

**Authentication Required:** No (public)

**Response:** HTML page with project information

---

#### Landing Page
**GET** `/landing`

Returns the marketing landing page.

**Authentication Required:** No (public)

**Response:** HTML standalone landing page

---

## Request/Response Formats

### Student Profile Schema

All 30 features required for prediction:

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `school` | string | `"GP"`, `"MS"` | Student's school |
| `sex` | string | `"F"`, `"M"` | Student's sex |
| `age` | integer | `15-22` | Student's age |
| `address` | string | `"U"`, `"R"` | Home address type |
| `famsize` | string | `"GT3"`, `"LE3"` | Family size |
| `Pstatus` | string | `"T"`, `"A"` | Parent's cohabitation status |
| `Medu` | integer | `0-4` | Mother's education |
| `Fedu` | integer | `0-4` | Father's education |
| `Mjob` | string | `"teacher"`, `"health"`, `"services"`, `"at_home"`, `"other"` | Mother's job |
| `Fjob` | string | `"teacher"`, `"health"`, `"services"`, `"at_home"`, `"other"` | Father's job |
| `reason` | string | `"home"`, `"reputation"`, `"course"`, `"other"` | Reason to choose school |
| `guardian` | string | `"mother"`, `"father"`, `"other"` | Student's guardian |
| `traveltime` | integer | `1-4` | Home to school travel time |
| `studytime` | integer | `1-4` | Weekly study time |
| `failures` | integer | `0-4` | Number of past class failures |
| `schoolsup` | string | `"yes"`, `"no"` | Extra educational support |
| `famsup` | string | `"yes"`, `"no"` | Family educational support |
| `paid` | string | `"yes"`, `"no"` | Extra paid classes |
| `activities` | string | `"yes"`, `"no"` | Extra-curricular activities |
| `nursery` | string | `"yes"`, `"no"` | Attended nursery school |
| `higher` | string | `"yes"`, `"no"` | Wants higher education |
| `internet` | string | `"yes"`, `"no"` | Internet access at home |
| `romantic` | string | `"yes"`, `"no"` | In romantic relationship |
| `famrel` | integer | `1-5` | Quality of family relationships |
| `freetime` | integer | `1-5` | Free time after school |
| `goout` | integer | `1-5` | Going out with friends |
| `Dalc` | integer | `1-5` | Workday alcohol consumption |
| `Walc` | integer | `1-5` | Weekend alcohol consumption |
| `health` | integer | `1-5` | Current health status |
| `absences` | integer | `0-93` | Number of school absences |
| `G1` | integer | `0-20` | First period grade |
| `G2` | integer | `0-20` | Second period grade |
| `custom_prompt` | string | (optional) | Custom advice request |

---

## Error Handling

### Error Response Format
```json
{
    "error": "Error description"
}
```

### Common Errors

#### 400 Bad Request
```json
{
    "error": "Missing required field: G1"
}
```

#### 429 Too Many Requests
```json
{
    "error": "Rate limit exceeded. Please try again later."
}
```

#### 500 Internal Server Error
```json
{
    "error": "An unexpected error occurred. Please try again."
}
```

---

## Rate Limiting

The API implements rate limiting to prevent abuse:

### Global Rate Limit
- **60 requests per minute** per IP address

### Prediction Endpoint
- **30 requests per minute** per IP address for `/api/predict`

### Rate Limit Headers
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1635789600
```

### Handling Rate Limits
When rate limit is exceeded, wait until the `X-RateLimit-Reset` timestamp before retrying.

---

## Examples

### Example 1: Basic Prediction Request

**cURL:**
```bash
curl -X POST http://localhost:8501/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "school": "GP",
    "sex": "F",
    "age": 17,
    "address": "U",
    "famsize": "GT3",
    "Pstatus": "T",
    "Medu": 3,
    "Fedu": 2,
    "Mjob": "services",
    "Fjob": "other",
    "reason": "course",
    "guardian": "mother",
    "traveltime": 2,
    "studytime": 2,
    "failures": 0,
    "schoolsup": "yes",
    "famsup": "yes",
    "paid": "no",
    "activities": "yes",
    "nursery": "yes",
    "higher": "yes",
    "internet": "yes",
    "romantic": "no",
    "famrel": 4,
    "freetime": 3,
    "goout": 2,
    "Dalc": 1,
    "Walc": 1,
    "health": 3,
    "absences": 5,
    "G1": 14,
    "G2": 15
  }'
```

**JavaScript (Fetch API):**
```javascript
async function predictRisk(studentData) {
    try {
        const response = await fetch('http://localhost:8501/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(studentData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('Risk Level:', result.prediction);
        console.log('Confidence:', result.confidence);
        console.log('Advice:', result.mentoring_advice);
        
        return result;
    } catch (error) {
        console.error('Prediction error:', error);
        throw error;
    }
}

// Usage
const studentProfile = {
    school: "GP",
    sex: "F",
    age: 17,
    // ... other fields
    G1: 14,
    G2: 15
};

predictRisk(studentProfile);
```

**Python (requests):**
```python
import requests

def predict_risk(student_data):
    url = "http://localhost:8501/api/predict"
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=student_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Risk Level: {result['prediction']}")
        print(f"Confidence: {result['confidence']}")
        return result
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

# Usage
student_profile = {
    "school": "GP",
    "sex": "F",
    "age": 17,
    # ... other fields
    "G1": 14,
    "G2": 15
}

result = predict_risk(student_profile)
```

---

### Example 2: Prediction with Custom Advice

```javascript
const studentData = {
    // ... all required fields
    G1: 10,
    G2: 11,
    custom_prompt: "Focus on math improvement strategies and stress management techniques"
};

const result = await fetch('/api/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(studentData)
}).then(res => res.json());

console.log(result.mentoring_advice);
// Output includes custom-tailored advice based on the prompt
```

---

### Example 3: Handling Rate Limits

```javascript
async function predictWithRetry(studentData, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(studentData)
            });
            
            if (response.status === 429) {
                const resetTime = response.headers.get('X-RateLimit-Reset');
                const waitTime = (resetTime * 1000) - Date.now();
                console.log(`Rate limited. Waiting ${waitTime}ms...`);
                await new Promise(resolve => setTimeout(resolve, waitTime));
                continue;
            }
            
            return await response.json();
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
    }
}
```

---

## Technical Implementation

### Machine Learning Pipeline
1. **Input Validation**: Check all 30 features are present
2. **Preprocessing**: Transform categorical variables, scale numerical features
3. **Prediction**: LightGBM model generates risk classification
4. **Explainability**: SHAP values calculated for top features
5. **Visualization**: Generate SHAP chart as base64-encoded PNG
6. **AI Advice**: Gemini 2.0 Flash generates personalized mentoring strategies

### Tech Stack
- **Backend**: Flask (Python)
- **ML Model**: LightGBM
- **Explainability**: SHAP
- **AI**: Google Gemini 2.0 Flash API
- **Auth**: Firebase Authentication
- **Database**: Firebase Firestore
- **Rate Limiting**: Flask-Limiter

---

## Security Considerations

1. **Input Validation**: All inputs are validated before processing
2. **Rate Limiting**: Prevents API abuse
3. **Firebase Auth**: Secure user authentication
4. **HTTPS**: Use HTTPS in production
5. **CORS**: Configure CORS policies appropriately
6. **Sensitive Data**: SHAP charts can hide sensitive features (age, sex)

---

## Support

For API issues or questions:
- GitHub Issues: [https://github.com/yourusername/student-risk-demo/issues](https://github.com/yourusername/student-risk-demo/issues)
- Documentation: See `USER_GUIDE.md` and `DEPLOYMENT.md`

---

**Last Updated:** October 2024  
**API Version:** 1.0.0
