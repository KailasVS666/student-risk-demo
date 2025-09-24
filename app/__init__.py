import os
import json
from flask import Flask
from flask_cors import CORS
import joblib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- ML Model Loading ---
# Load models globally so they are accessible to the app
try:
    model_pipeline = joblib.load('early_warning_model_pipeline.joblib')
    core_model = joblib.load('student_risk_classifier.joblib')
except FileNotFoundError:
    print("Model files not found. Please run 'python train_model.py' first.")
    model_pipeline = None
    core_model = None


def create_app():
    """Application factory function."""
    app = Flask(__name__)
    CORS(app)

    # Make models and API keys available to the app's context
    app.config['MODEL_PIPELINE'] = model_pipeline
    app.config['CORE_MODEL'] = core_model

    # Load Gemini API Key from .env file
    # Note: Your .env file uses 'GEMINI_API_KEY', not 'GOOGLE_API_KEY'
    app.config['GEMINI_API_KEY'] = os.getenv("GEMINI_API_KEY")

    # Load and parse the Firebase config string from the .env file
    firebase_config_str = os.getenv('FIREBASE_CONFIG')
    if firebase_config_str:
        try:
            app.config['FIREBASE_CONFIG'] = json.loads(firebase_config_str)
        except json.JSONDecodeError:
            print("Error: Could not parse FIREBASE_CONFIG from .env file. Ensure it is a valid JSON string on one line.")
            app.config['FIREBASE_CONFIG'] = {}
    else:
        app.config['FIREBASE_CONFIG'] = {}
    
    # Import and register the blueprint from routes.py
    with app.app_context():
        from . import routes
        app.register_blueprint(routes.main_bp)

    return app