from flask import Flask
from flask_cors import CORS
import os
import joblib
import shap
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- ML Model Loading ---
# Load models globally so they are accessible to the app
model_pipeline = joblib.load('early_warning_model_pipeline.joblib')
core_model = joblib.load('student_risk_classifier.joblib')

def create_app():
    """Application factory function."""
    app = Flask(__name__)
    CORS(app)

    # Make models and API keys available to the app's context
    app.config['MODEL_PIPELINE'] = model_pipeline
    app.config['CORE_MODEL'] = core_model
    app.config['GEMINI_API_KEY'] = os.getenv("GOOGLE_API_KEY")
    
    # Load Firebase config into the app's context
    app.config['FIREBASE_CONFIG'] = {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID"),
    }

    # Import and register the blueprint from routes.py
    with app.app_context():
        from . import routes
        app.register_blueprint(routes.main_bp)

    return app