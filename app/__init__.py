from flask import Flask
from flask_cors import CORS
import joblib
import os
from dotenv import load_dotenv
import pandas as pd

def create_app():
    """
    Creates and configures an instance of the Flask application.
    This is the main factory function for the application.
    """
    # Load environment variables from a .env file
    load_dotenv()

    # Initialize the Flask app
    app = Flask(__name__)
    
    # Enable Cross-Origin Resource Sharing (CORS) to allow your frontend
    # to communicate with the Flask backend.
    CORS(app)

    # --- Load Configuration and Models ---
    # It's much more efficient to load these once at startup rather than in every request.
    with app.app_context():
        # Load the Firebase config from environment variables
        app.config['FIREBASE_CONFIG'] = {
            "apiKey": os.getenv("FIREBASE_API_KEY"),
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
            "projectId": os.getenv("FIREBASE_PROJECT_ID"),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.getenv("FIREBASE_APP_ID")
        }
        
        # Load the Gemini API Key
        app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')

        try:
            # Load the machine learning models and encoders
            app.config['MODEL_PIPELINE'] = joblib.load('early_warning_model_pipeline_tuned.joblib')
            app.config['LABEL_ENCODER'] = joblib.load('label_encoder.joblib')
            app.config['CORE_MODEL'] = joblib.load('student_risk_classifier_tuned.joblib')
            print("All models loaded successfully.")

            # Pre-load and calculate grade averages for efficiency
            df = pd.read_csv('student-por.csv', sep=';')
            app.config['GRADE_AVERAGES'] = df[['G1', 'G2']].mean().to_dict()
            print("Grade averages calculated and cached.")

        except FileNotFoundError as e:
            print(f"Error loading model or data file: {e}")
            print("Please ensure that the .joblib and .csv files are in the root directory.")
        
        # --- Register Blueprints ---
        # Blueprints help organize the application's routes.
        from . import routes
        app.register_blueprint(routes.main_bp)
        print("Routes blueprint registered.")

    return app