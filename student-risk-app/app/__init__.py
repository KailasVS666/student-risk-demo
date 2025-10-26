import os
import json
import joblib
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from .limits import limiter
from dotenv import load_dotenv

# Add these imports for the class
from sklearn.base import BaseEstimator, TransformerMixin

# Define the ColumnDropper class here so joblib can find it
class ColumnDropper(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return X.drop(columns=self.columns, errors='ignore')

def create_app():
    load_dotenv()

    # --- Structured Logging Setup ---
    # Console + rotating file logs at INFO level by default
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger()
    if not logger.handlers:
        logger.setLevel(log_level)

        formatter = logging.Formatter(
            fmt='%(asctime)s %(levelname)s %(name)s - %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # Rotating file handler (logs/app.log)
        logs_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        fh = RotatingFileHandler(os.path.join(logs_dir, 'app.log'), maxBytes=1_000_000, backupCount=3)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    # --- Validate Critical Environment Variables ---
    required_env_vars = [
        'GEMINI_API_KEY',
        'FIREBASE_API_KEY',
        'FIREBASE_AUTH_DOMAIN',
        'FIREBASE_PROJECT_ID',
        'FIREBASE_STORAGE_BUCKET',
        'FIREBASE_MESSAGING_SENDER_ID',
        'FIREBASE_APP_ID'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(
            f"\n{'='*60}\n"
            f"ERROR: Missing required environment variables!\n"
            f"{'='*60}\n"
            f"Missing: {', '.join(missing_vars)}\n\n"
            f"Please create a .env file with all required variables.\n"
            f"See README.md for setup instructions.\n"
            f"{'='*60}\n"
        )
    
    logging.info("All required environment variables found.")

    app = Flask(__name__)
    # Initialize rate limiter
    try:
        limiter.init_app(app)
        logging.info("Rate limiter initialized (60/min default per IP).")
    except Exception as e:
        logging.warning(f"Rate limiter initialization failed: {e}")

    # --- Load Machine Learning Models ---
    try:
        app.config['MODEL_PIPELINE'] = joblib.load('early_warning_model_pipeline_tuned.joblib')
        app.config['LABEL_ENCODER'] = joblib.load('label_encoder.joblib')
        app.config['CORE_MODEL'] = joblib.load('student_risk_classifier_tuned.joblib')
        logging.info("All models loaded successfully.")
    except FileNotFoundError:
        logging.warning("Model files not found! Make sure to run train_model.py first.")
        # Exit or handle as appropriate
    except Exception as e:
        logging.exception(f"Error loading models: {e}")

    # --- Load Pre-calculated Averages ---
    try:
        with open('grade_averages.json', 'r') as f:
            app.config['GRADE_AVERAGES'] = json.load(f)
        logging.info("Grade averages calculated and cached.")
    except FileNotFoundError:
        # This is not critical, can be calculated on the fly if needed
        app.config['GRADE_AVERAGES'] = {}
        logging.info("Grade averages JSON not found. Will calculate on the fly.")

    # --- Firebase Configuration ---
    firebase_config = {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID"),
        "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
    }
    app.config['FIREBASE_CONFIG'] = json.dumps(firebase_config)

    # --- Gemini Configuration ---
    app.config['GEMINI_API_KEY'] = os.getenv("GEMINI_API_KEY")

    #
    # >>>>> THIS IS THE CORRECT FIX <<<<<
    #
    # --- Register Blueprints (Routes) ---
    # Change 'routes' back to 'main' to match the variable in routes.py
    from .routes import main as routes_blueprint  # Corrected import
    app.register_blueprint(routes_blueprint)
    logging.info("Routes blueprint registered.")

    return app