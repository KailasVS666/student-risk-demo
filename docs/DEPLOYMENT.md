# Deployment Guide - AI Student Mentor

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Environment Configuration](#environment-configuration)
4. [Deployment Options](#deployment-options)
5. [Render.com Deployment](#rendercom-deployment)
6. [Railway.app Deployment](#railwayapp-deployment)
7. [Azure App Service Deployment](#azure-app-service-deployment)
8. [Post-Deployment Configuration](#post-deployment-configuration)
9. [Monitoring & Maintenance](#monitoring--maintenance)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts
- **Firebase Account** (Free Spark Plan)
  - Firebase Authentication enabled
  - Firestore Database created
- **Google Cloud Account** (for Gemini API)
  - Gemini 2.0 Flash API key
- **Deployment Platform** (choose one):
  - Render.com (Free tier)
  - Railway.app (Free tier)
  - Azure (F1 Free tier)

### Local Requirements
- Python 3.8+ installed
- Git installed
- Code editor (VS Code recommended)

---

## Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/student-risk-demo.git
cd student-risk-demo/student-risk-app
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables
Create a `.env` file in the `student-risk-app/` directory:

```env
# Firebase Configuration
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=1:123456789:web:abcdef
FIREBASE_MEASUREMENT_ID=G-ABCDEF

# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_secret_key_here
```

### 5. Run Locally
```bash
python run.py
```

Visit `http://127.0.0.1:8501` in your browser.

### 6. Tailwind CSS (UI styles)

For production, Tailwind is compiled to `app/static/css/tw-build.css`.

- Quick dev fallback: if the compiled file is missing, the app will load the Tailwind CDN automatically, suitable for local development only.
- Recommended: install Node and build the CSS before running in production.

```bash
npm install
npm run tailwind:build
```

This generates `app/static/css/tw-build.css` consumed by the templates.

---

## Environment Configuration

### Firebase Setup

#### 1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add Project"
3. Enter project name: `student-risk-mentor` (or your choice)
4. Disable Google Analytics (optional for prototype)
5. Click "Create Project"

#### 2. Enable Authentication
1. In Firebase Console, go to **Authentication**
2. Click "Get Started"
3. Enable **Email/Password** sign-in method
4. Save changes

#### 3. Create Firestore Database
1. In Firebase Console, go to **Firestore Database**
2. Click "Create Database"
3. Choose **Start in test mode** (for development)
4. Select Cloud Firestore location (choose nearest to your users)
5. Click "Enable"

#### 4. Get Firebase Config
1. Go to **Project Settings** (gear icon)
2. Scroll to "Your apps"
3. Click "Web" icon (</>) to register a web app
4. Enter app nickname: `student-risk-web`
5. Copy the `firebaseConfig` object values to your `.env` file

### Gemini API Setup

#### 1. Get API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Get API Key"
3. Create new API key or use existing
4. Copy key to `GEMINI_API_KEY` in `.env` file

#### 2. Free Tier Limits
- **1,500 requests per day** for Gemini 2.0 Flash
- No credit card required
- Rate limit: 15 RPM (requests per minute)

---

## Deployment Options

### Comparison Table

| Platform | Free Tier | Pros | Cons | Best For |
|----------|-----------|------|------|----------|
| **Render.com** | 750 hrs/month | Easy setup, Auto-deploy from Git, Free SSL | Cold starts (~30s), Sleeps after inactivity | Quick prototypes |
| **Railway.app** | $5 free credit/month | Fast deployments, Good UI, No cold starts | Limited free credit | Active development |
| **Azure App Service** | F1 tier (60 min CPU/day) | Microsoft integration, Scalable | Complex setup, Limited free tier | Enterprise projects |

---

## Render.com Deployment

### Step 1: Prepare Repository
Ensure your project has these files in the root:

**`requirements.txt`**
```
Flask==3.0.0
lightgbm==4.1.0
shap==0.43.0
google-generativeai==0.3.2
firebase-admin==6.3.0
Flask-Limiter==3.5.0
python-dotenv==1.0.0
numpy==1.24.3
pandas==2.1.3
scikit-learn==1.3.2
matplotlib==3.8.2
Pillow==10.1.0
gunicorn==21.2.0
```

**`Procfile`** (create in project root):
```
web: cd student-risk-app && gunicorn run:app
```

### Step 2: Create Render Web Service
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure settings:
   - **Name**: `student-risk-mentor`
   - **Environment**: Python 3
   - **Build Command**: `bash build.sh`
   - **Start Command**: `gunicorn run:app --bind 0.0.0.0:$PORT`
   - **Plan**: Free

> **⚠️ Important**: The `build.sh` script will automatically train the ML models on first deployment. This may take 2-3 minutes. Subsequent deployments will skip model training if the files already exist.

### Step 3: Add Environment Variables
In Render dashboard, go to "Environment" tab and add:

```
FIREBASE_API_KEY=your_value
FIREBASE_AUTH_DOMAIN=your_value
FIREBASE_PROJECT_ID=your_value
FIREBASE_STORAGE_BUCKET=your_value
FIREBASE_MESSAGING_SENDER_ID=your_value
FIREBASE_APP_ID=your_value
FIREBASE_MEASUREMENT_ID=your_value
GEMINI_API_KEY=your_value
FLASK_ENV=production
SECRET_KEY=your_secret_key
```

### Step 4: Deploy
1. Click "Create Web Service"
2. Render will automatically run `build.sh` which:
   - Installs Python and Node dependencies
   - Trains the ML models (first deploy only, ~2-3 minutes)
   - Builds the Tailwind CSS
   - Starts the Flask app
3. Watch the deployment logs (should see "Models trained successfully" on first deploy)
4. Wait 10-15 minutes for first deployment (includes model training time)
5. Access your app at: `https://student-risk-mentor.onrender.com`

### Step 5: Auto-Deploy Setup
- Render automatically deploys on Git push to main branch
- Configure deploy hooks in Render dashboard if needed

### Troubleshooting Render Deployments

#### Issue: 502 Bad Gateway on `/api/predict`
**Cause**: Models failed to load or training timed out
**Solution**: 
1. Check Render deployment logs for training errors
2. Ensure CSV files (`student-mat.csv`, `student-por.csv`) are in repo
3. If training times out, pre-train models locally and commit them (track with Git LFS)

#### Issue: Application won't start
**Cause**: Missing environment variables
**Solution**:
1. Check Render dashboard for incomplete env vars
2. Ensure all Firebase and Gemini API keys are set
3. Redeploy after adding missing variables

---

## Railway.app Deployment

### Step 1: Install Railway CLI (Optional)
```bash
npm install -g @railway/cli
railway login
```

### Step 2: Deploy via Dashboard
1. Go to [Railway Dashboard](https://railway.app/)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway auto-detects Python and builds

### Step 3: Configure Environment Variables
In Railway dashboard:
1. Click on your service
2. Go to "Variables" tab
3. Add all Firebase and Gemini environment variables

### Step 4: Configure Start Command
In "Settings" tab:
- **Start Command**: `cd student-risk-app && gunicorn run:app --bind 0.0.0.0:$PORT`

### Step 5: Generate Domain
1. Go to "Settings" → "Networking"
2. Click "Generate Domain"
3. Access your app at: `https://your-app.up.railway.app`

---

## Azure App Service Deployment

### Prerequisites
- Azure account (free tier)
- Azure CLI installed

### Step 1: Install Azure CLI
```bash
# Windows (PowerShell)
winget install Microsoft.AzureCLI

# macOS
brew install azure-cli

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### Step 2: Login to Azure
```bash
az login
```

### Step 3: Create Resource Group
```bash
az group create --name student-risk-rg --location eastus
```

### Step 4: Create App Service Plan (Free Tier)
```bash
az appservice plan create \
  --name student-risk-plan \
  --resource-group student-risk-rg \
  --sku F1 \
  --is-linux
```

### Step 5: Create Web App
```bash
az webapp create \
  --resource-group student-risk-rg \
  --plan student-risk-plan \
  --name student-risk-mentor \
  --runtime "PYTHON:3.11"
```

### Step 6: Configure Environment Variables
```bash
az webapp config appsettings set \
  --resource-group student-risk-rg \
  --name student-risk-mentor \
  --settings \
    FIREBASE_API_KEY="your_value" \
    FIREBASE_AUTH_DOMAIN="your_value" \
    FIREBASE_PROJECT_ID="your_value" \
    FIREBASE_STORAGE_BUCKET="your_value" \
    FIREBASE_MESSAGING_SENDER_ID="your_value" \
    FIREBASE_APP_ID="your_value" \
    FIREBASE_MEASUREMENT_ID="your_value" \
    GEMINI_API_KEY="your_value" \
    FLASK_ENV="production" \
    SECRET_KEY="your_secret_key"
```

### Step 7: Deploy Code
```bash
# From project root
cd student-risk-app
az webapp up \
  --resource-group student-risk-rg \
  --name student-risk-mentor \
  --runtime "PYTHON:3.11"
```

### Step 8: Configure Startup Command
```bash
az webapp config set \
  --resource-group student-risk-rg \
  --name student-risk-mentor \
  --startup-file "gunicorn run:app"
```

### Step 9: Access Application
Visit: `https://student-risk-mentor.azurewebsites.net`

---

## Post-Deployment Configuration

### 1. Update Firebase Authorized Domains
1. Go to Firebase Console → Authentication → Settings
2. Under "Authorized domains", add:
   - Your Render/Railway/Azure domain
   - Example: `student-risk-mentor.onrender.com`

### 2. Update Firestore Security Rules
In Firebase Console → Firestore → Rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow users to read/write their own profiles
    match /profiles/{userEmail}/student_data/{document=**} {
      allow read, write: if request.auth != null && request.auth.token.email == userEmail;
    }
    
    // Deny all other access
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

### 3. Configure CORS (if needed)
In `app/__init__.py`, add:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://your-domain.com"],
        "methods": ["POST", "GET"],
        "allow_headers": ["Content-Type"]
    }
})
```

### 4. Enable HTTPS (Production)
Most platforms (Render, Railway, Azure) provide free SSL certificates automatically.

---

## Monitoring & Maintenance

### Logging
Monitor application logs in your platform's dashboard:

**Render:**
```bash
# View logs in dashboard or CLI
render logs
```

**Railway:**
- View logs in dashboard under "Deployments" tab

**Azure:**
```bash
az webapp log tail --resource-group student-risk-rg --name student-risk-mentor
```

### Health Checks
Create a health endpoint in `app/routes.py`:

```python
@main_bp.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200
```

### Performance Monitoring
- Use Firebase Analytics for user tracking
- Monitor API usage in Google Cloud Console (Gemini API)
- Check Firestore usage in Firebase Console

### Backup Strategy
- Firebase Firestore exports (use Firebase CLI)
- Export user data via Settings page in app
- Store ML models in version control

---

## Troubleshooting

### Issue: Cold Starts (Render/Railway)
**Symptom:** App takes 30+ seconds to load after inactivity

**Solutions:**
- Use a service like [UptimeRobot](https://uptimerobot.com/) to ping your app every 5 minutes
- Upgrade to paid tier for always-on instances

---

### Issue: Rate Limit Exceeded (Gemini API)
**Symptom:** "Rate limit exceeded" errors

**Solutions:**
- Implement request queuing
- Cache responses for identical requests
- Upgrade to paid Gemini API tier

---

### Issue: Firebase Authentication Fails
**Symptom:** Users can't log in

**Solutions:**
- Verify Firebase config environment variables are correct
- Check authorized domains in Firebase Console
- Ensure Firebase Auth is enabled for Email/Password

---

### Issue: Model Loading Errors
**Symptom:** "Model file not found" or import errors

**Solutions:**
- Verify `.joblib` files are in correct directory
- Check file paths in `app/__init__.py`
- Ensure models are included in deployment (not in `.gitignore`)

---

### Issue: Firestore Permission Denied
**Symptom:** Can't save/load profiles

**Solutions:**
- Update Firestore security rules (see Post-Deployment Configuration)
- Verify user is authenticated
- Check Firebase console for error logs

---

## Performance Optimization

### 1. Caching
Implement Flask-Caching for repeated predictions:

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.memoize(timeout=300)
def generate_prediction(data_hash):
    # Prediction logic
    pass
```

### 2. Async Processing
Use background tasks for Gemini API calls:

```python
from threading import Thread

def async_advice(data):
    # Generate advice in background
    pass

Thread(target=async_advice, args=(data,)).start()
```

### 3. CDN for Static Assets
Use a CDN for Tailwind CSS and Chart.js instead of local hosting.

---

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use strong SECRET_KEY** for Flask sessions
3. **Enable HTTPS** in production
4. **Implement CSRF protection** for forms
5. **Sanitize user inputs** before database storage
6. **Rotate API keys** regularly
7. **Monitor Firebase usage** for unusual activity

---

## Scaling Considerations

### When to Upgrade
- **Free Tier Limits Reached**: More than 750 hours/month (Render) or $5 credit (Railway)
- **High Traffic**: More than 1,500 Gemini requests/day
- **Database Growth**: Firestore free tier exceeded (1GB storage, 50K reads/day)

### Upgrade Paths
- **Render Pro**: $7/month (no cold starts, more resources)
- **Railway Pro**: $20/month (no credit limits, priority support)
- **Azure B1 Basic**: ~$13/month (1.75GB RAM, no daily CPU limits)
- **Gemini API Pay-as-you-go**: $0.00025 per request

---

## Additional Resources

- [Flask Deployment Documentation](https://flask.palletsprojects.com/en/3.0.x/deploying/)
- [Render.com Docs](https://render.com/docs)
- [Railway.app Docs](https://docs.railway.app/)
- [Azure App Service Docs](https://learn.microsoft.com/en-us/azure/app-service/)
- [Firebase Documentation](https://firebase.google.com/docs)
- [Gemini API Documentation](https://ai.google.dev/docs)

---

## Support

For deployment issues:
- Check platform-specific documentation
- Open an issue on [GitHub](https://github.com/yourusername/student-risk-demo/issues)
- Review logs for error details

---

**Last Updated:** October 2024  
**Version:** 1.0.0
