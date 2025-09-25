import os
import json
from flask import Flask
from flask_cors import CORS
import joblib
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app():
    """Application factory function."""
    app = Flask(__name__)
    CORS(app)

    # --- Load ML Models and Encoder ---
    try:
        # Load the TUNED models and the new label encoder
        model_pipeline = joblib.load('early_warning_model_pipeline_tuned.joblib')
        core_model = joblib.load('student_risk_classifier_tuned.joblib')
        label_encoder = joblib.load('label_encoder.joblib')
    except FileNotFoundError as e:
        print(f"Error loading model files: {e}")
        print("Please ensure you have run 'python train_model.py' successfully.")
        # Set to None so the app can still start, but prediction routes will fail
        model_pipeline = None
        core_model = None
        label_encoder = None

    # --- App Configuration ---
    # Make models and encoder available to the app's context
    app.config['MODEL_PIPELINE'] = model_pipeline
    app.config['CORE_MODEL'] = core_model
    app.config['LABEL_ENCODER'] = label_encoder

    # Load Gemini API Key
    app.config['GEMINI_API_KEY'] = os.getenv("GEMINI_API_KEY")

    # Load and parse the Firebase config from the .env file
    firebase_config_str = os.getenv('FIREBASE_CONFIG')
    if firebase_config_str:
        try:
            app.config['FIREBASE_CONFIG'] = json.loads(firebase_config_str)
        except json.JSONDecodeError:
            print("Error: Could not parse FIREBASE_CONFIG. Ensure it is a valid JSON string.")
            app.config['FIREBASE_CONFIG'] = {}
    else:
        app.config['FIREBASE_CONFIG'] = {}
    
    # Import and register the blueprint from routes.py
    with app.app_context():
        from . import routes
        app.register_blueprint(routes.main_bp)

    return app