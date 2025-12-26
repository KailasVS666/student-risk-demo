import os
import json
import joblib
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_mail import Mail
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from .limits import limiter
from dotenv import load_dotenv

# Add these imports for the class
from sklearn.base import BaseEstimator, TransformerMixin

# Define Global Extensions
mail = Mail()  # Initialize Mail globally
csrf = CSRFProtect()  # Initialize CSRF protection globally

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
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger()
    if not logger.handlers:
        logger.setLevel(log_level)
        formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s %(name)s - %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # Rotating file handler
        logs_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        fh = RotatingFileHandler(os.path.join(logs_dir, 'app.log'), maxBytes=1_000_000, backupCount=3)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    # --- Validate Environment Variables ---
    # Critical variables (App will fail without these)
    critical_vars = [
        'GEMINI_API_KEY', 'FIREBASE_API_KEY', 'FIREBASE_AUTH_DOMAIN',
        'FIREBASE_PROJECT_ID', 'FIREBASE_STORAGE_BUCKET',
        'FIREBASE_MESSAGING_SENDER_ID', 'FIREBASE_APP_ID'
    ]
    
    # Notification variables (App works, but alerts won't send)
    mail_vars = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD']
    
    # Check critical vars
    missing_critical = [var for var in critical_vars if not os.getenv(var)]
    if missing_critical:
        raise EnvironmentError(f"ERROR: Missing critical env vars: {', '.join(missing_critical)}")

    # Check mail vars (Soft check)
    missing_mail = [var for var in mail_vars if not os.getenv(var)]
    if missing_mail:
        logging.warning(f"Missing email configuration: {', '.join(missing_mail)}. Faculty alerts will not be sent.")

    logging.info("Environment check complete.")

    app = Flask(__name__)
    
    # --- Security Configuration ---
    # CSRF Protection
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Only protect routes that explicitly need it
    app.config['WTF_CSRF_TIME_LIMIT'] = None  # No token expiry
    csrf.init_app(app)
    
    # Security Headers (CSP, X-Frame-Options, etc.)
    Talisman(
        app,
        force_https=os.getenv('ENVIRONMENT', 'development') == 'production',
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,  # 1 year
        content_security_policy={
            'default-src': "'self'",
            'script-src': ["'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'cdn.tailwindcss.com', 'www.gstatic.com', 'www.googleapis.com'],
            'style-src': ["'self'", "'unsafe-inline'", 'cdn.tailwindcss.com', 'fonts.googleapis.com'],
            'img-src': ["'self'", 'data:', 'https:'],
            'font-src': ["'self'", 'fonts.gstatic.com'],
            'connect-src': ["'self'", 'firebaseio.com', '*.firebaseio.com', 'firebase.googleapis.com', '*.google.com', 'generativelanguage.googleapis.com'],
            'frame-ancestors': "'none'",
            'base-uri': "'self'",
            'form-action': "'self'"
        },
        content_security_policy_nonce_in=['script-src']
    )
    
    # Session Configuration (for CSRF tokens)
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('ENVIRONMENT', 'development') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    
    # SECRET_KEY for session management (required for Flask-WTF)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32).hex())
    
    # --- Mail Configuration (For High-Risk Alerts) ---
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

    # Initialize Extensions
    try:
        limiter.init_app(app)
        mail.init_app(app)  # Bind mail to app
        logging.info("Extensions (Limiter, Mail) initialized.")
    except Exception as e:
        logging.warning(f"Extension initialization failed: {e}")

    # --- Load Machine Learning Models ---
    try:
        app.config['MODEL_PIPELINE'] = joblib.load('early_warning_model_pipeline_tuned.joblib')
        app.config['LABEL_ENCODER'] = joblib.load('label_encoder.joblib')
        app.config['CORE_MODEL'] = joblib.load('student_risk_classifier_tuned.joblib')
        logging.info("All models loaded successfully.")
    except FileNotFoundError:
        logging.warning("Model files not found! Make sure to run train_model.py first.")
    except Exception as e:
        logging.exception(f"Error loading models: {e}")

    # --- Load Pre-calculated Averages ---
    try:
        with open('grade_averages.json', 'r') as f:
            app.config['GRADE_AVERAGES'] = json.load(f)
        logging.info("Grade averages calculated and cached.")
    except FileNotFoundError:
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
    app.config['GEMINI_API_KEY'] = os.getenv("GEMINI_API_KEY")

    # --- Register Blueprints ---
    from .routes import main_bp as api_routes_bp
    from .views.auth import auth_bp
    from .views.dashboard import dashboard_bp
    from .views.assessment import assessment_bp
    from .views.history import history_bp
    from .views.other import other_bp
    
    app.register_blueprint(api_routes_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(other_bp)
    
    logging.info("All route blueprints registered successfully.")

    return app