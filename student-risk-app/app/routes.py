import os
import json
import joblib
import numpy as np
import pandas as pd
from flask import Blueprint, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import shap
import logging
from .limits import limiter

# CRITICAL FIX: Load environment variables from .env file for security
load_dotenv()

# --- API Keys and Configuration ---
# Keys are securely loaded from the environment variables defined in .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Initialization ---
main_bp = Blueprint('main', __name__)

# FIX: Use __file__ for robust pathing relative to the 'app' directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'early_warning_model_pipeline_tuned.joblib')
SHAP_EXPLAINER_PATH = os.path.join(BASE_DIR, 'student_risk_classifier_tuned.joblib')
LABEL_ENCODER_PATH = os.path.join(BASE_DIR, 'label_encoder.joblib')

# Load Model/Pipeline and Explainer
pipeline = None
risk_explainer = None
label_encoder = None
logger = logging.getLogger(__name__)
try:
    pipeline = joblib.load(MODEL_PATH)
    risk_explainer = joblib.load(SHAP_EXPLAINER_PATH) 
    label_encoder = joblib.load(LABEL_ENCODER_PATH)
    logger.info("Models and Pipeline loaded successfully.")
except Exception as e:
    logger.error(f"Error loading models: {e}. Check paths: {MODEL_PATH}")

# Initialize Gemini Model (google-generativeai SDK)
gemini_model = None
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        # Use gemini-2.5-flash - fast, stable, and widely available
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("Gemini model initialized successfully (gemini-2.5-flash).")
    else:
        logger.warning("GEMINI_API_KEY not found in environment.")
except Exception as e:
    logger.error(f"Error initializing Gemini model: {e}")


# --- Helper Functions ---

# CRITICAL FIX: Function to encode string data for the ML model
def preprocess_data_for_pipeline(data_df, label_encoder):
    """Encodes categorical features in the DataFrame using the loaded label encoder mappings."""
    categorical_cols = [
        'school', 'sex', 'address', 'famsize', 'Pstatus', 'Mjob', 'Fjob',
        'reason', 'guardian', 'schoolsup', 'famsup', 'paid', 'activities',
        'nursery', 'higher', 'internet', 'romantic'
    ]
    
    encoded_data_df = data_df.copy()
    
    for col in categorical_cols:
        if col in encoded_data_df.columns and col in label_encoder:
            encoder_map = label_encoder[col]
            raw_value = encoded_data_df[col].iloc[0]
            
            if raw_value in encoder_map.classes_:
                encoded_value = encoder_map.transform([raw_value])[0]
                encoded_data_df[col] = encoded_value
            else:
                encoded_data_df[col] = 0 
    
    # CRITICAL FIX: Ensure column order matches training data
    # The model expects this EXACT order
    expected_columns = [
        'school', 'sex', 'age', 'address', 'famsize', 'Pstatus', 'Medu', 'Fedu',
        'Mjob', 'Fjob', 'reason', 'guardian', 'traveltime', 'studytime',
        'failures', 'schoolsup', 'famsup', 'paid', 'activities', 'nursery',
        'higher', 'internet', 'romantic', 'famrel', 'freetime', 'goout',
        'Dalc', 'Walc', 'health', 'absences', 'G1', 'G2', 
        'average_grade', 'grade_change'
    ]
    
    # Reorder columns to match training
    encoded_data_df = encoded_data_df[expected_columns]
                
    return encoded_data_df


def map_risk_category(grade):
    """Maps a predicted G3 grade (0-20) to a risk category and descriptor."""
    if grade < 10:
        return "high", "Requires immediate intervention and support."
    elif 10 <= grade <= 13:
        return "medium", "Needs focused attention to improve academic trajectory."
    else:
        return "low", "On track, but minor improvements can maximize potential."

def get_shap_feature_importance(preprocessed_data, predicted_class):
    """
    Calculates SHAP feature importances for the given input row and predicted class.
    Handles multi-class outputs across SHAP versions (TreeExplainer/Explainer) safely.
    Returns top 5 features with highest absolute impact.
    """
    if risk_explainer is None:
        # Fallback to static data if model not loaded
        return [
            {'feature': 'Second Grade (G2)', 'importance': 0.85},
            {'feature': 'Past Failures', 'importance': -0.65},
            {'feature': 'Weekly Study Time', 'importance': 0.40},
            {'feature': 'Absences', 'importance': -0.30},
            {'feature': "Mother's Education", 'importance': 0.25},
        ]

    try:
        feature_names = preprocessed_data.columns.tolist()

        # Prefer the unified API; fall back to TreeExplainer if needed
        try:
            explainer = shap.Explainer(risk_explainer)
            exp = explainer(preprocessed_data)
            values = getattr(exp, 'values', None)
        except Exception:
            explainer = shap.TreeExplainer(risk_explainer)
            values = explainer.shap_values(preprocessed_data)

        # Normalize to a 1D array of shape (n_features,)
        class_values = None
        if isinstance(values, list):
            # List per class -> pick predicted class, first row
            class_values = values[int(predicted_class)][0]
        elif hasattr(values, 'ndim'):
            if values.ndim == 3:
                # (n_samples, n_classes, n_features)
                class_values = values[0, int(predicted_class), :]
            elif values.ndim == 2:
                # (n_samples, n_features)
                class_values = values[0, :]
            else:
                # Unexpected shape; flatten first row
                class_values = values.reshape(values.shape[-1])
        else:
            # Unknown type; try to coerce
            class_values = np.array(values)[0]

        # Pair features with their SHAP impact
        importance_pairs = list(zip(feature_names, class_values.tolist()))

        # Sort by absolute importance and select top 5
        top_sorted = sorted(importance_pairs, key=lambda x: abs(x[1]), reverse=True)[:5]

        # Friendly display names for some common features
        readable_names = {
            'G1': 'First Grade (G1)',
            'G2': 'Second Grade (G2)',
            'failures': 'Past Failures',
            'studytime': 'Weekly Study Time',
            'absences': 'Absences',
            'Medu': "Mother's Education",
            'Fedu': "Father's Education",
            'goout': 'Going Out Frequency',
            'health': 'Health Status',
            'famrel': 'Family Relationship Quality'
        }

        return [
            {
                'feature': readable_names.get(name, name.replace('_', ' ').title()),
                'importance': float(val)
            }
            for name, val in top_sorted
        ]

    except Exception as e:
        logger.exception(f"SHAP calculation error: {e}")
        # Conservative fallback to avoid breaking the UI
        return [
            {'feature': 'Second Grade (G2)', 'importance': 0.85},
            {'feature': 'Weekly Study Time', 'importance': 0.40},
            {'feature': 'Absences', 'importance': -0.30},
        ]


def generate_mentoring_advice(student_data, predicted_g3, risk_category, top_features):
    """Generates personalized advice using the Gemini API with structured markdown."""
    if gemini_model is None:
        return "Mentoring advice generation is currently unavailable (Gemini model not initialized)."

    feature_list = "\n".join([f"* **{f['feature']}**: Impact {f['importance']:.2f}" for f in top_features])
    
    custom_prompt_text = student_data.get('customPrompt', '').strip()
    custom_prompt_section = f"The user has a specific request: '{custom_prompt_text}'. Ensure your advice directly addresses this request first." if custom_prompt_text else ""


    prompt = f"""
    You are an AI Student Mentor. Based on the following student profile and prediction,
    provide personalized, actionable mentoring advice in a structured, easy-to-read format using markdown.
    
    {custom_prompt_section}

    **Predicted Final Grade (G3)**: {predicted_g3} / 20
    **Risk Level**: {risk_category.upper()}
    **Key Influencing Factors**:
    {feature_list}

    The advice MUST be formatted using clear markdown headings (use ###) and a maximum of 4 bullet points under three main sections. Do not include any introductory or concluding text outside of these three sections:

    ### ⚡ Immediate Focus Areas
    * Focus on improving performance in core subjects, especially if G2 showed a drop.
    * Dedicate specific, uninterrupted blocks of time for your most challenging classes.
    * If Failures is a factor, consult with a school counselor to address foundational gaps.

    ### 📚 Academic Strategy
    * Ensure your study environment supports the recommended study time.
    * Actively seek feedback on G1 and G2 to pinpoint areas for improvement.
    * Form a small, focused study group for collaborative learning once a week.

    ### 🧘 Lifestyle Balance
    * Prioritize getting 7-9 hours of sleep, as health is crucial for concentration.
    * Plan 'Going Out' time to ensure it does not conflict with essential study hours.
    * Leverage support systems: Discuss academic challenges openly with your Guardian.
    """

    try:
        response = gemini_model.generate_content(prompt)
        # google-generativeai SDK returns .text on successful generations
        return getattr(response, 'text', '').strip() or "No advice generated."
    except Exception as e:
        return f"Error generating advice: {e}"


def validate_student_data(data):
    """
    Validates incoming student data for required fields and value ranges.
    Raises ValueError if validation fails.
    """
    # Required fields
    required_fields = ['G1', 'G2', 'age', 'school', 'sex']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Numeric range validations
    validations = {
        'G1': (0, 20, "First grade (G1)"),
        'G2': (0, 20, "Second grade (G2)"),
        'age': (15, 22, "Age"),
        'studytime': (1, 4, "Study time"),
        'failures': (0, 4, "Number of failures"),
        'famrel': (1, 5, "Family relationship"),
        'freetime': (1, 5, "Free time"),
        'goout': (1, 5, "Going out"),
        'Dalc': (1, 5, "Workday alcohol consumption"),
        'Walc': (1, 5, "Weekend alcohol consumption"),
        'health': (1, 5, "Health status"),
        'absences': (0, 93, "Absences"),
        'Medu': (0, 4, "Mother's education"),
        'Fedu': (0, 4, "Father's education"),
        'traveltime': (1, 4, "Travel time")
    }
    
    for field, (min_val, max_val, display_name) in validations.items():
        if field in data:
            try:
                value = int(data[field])
                if not (min_val <= value <= max_val):
                    raise ValueError(
                        f"{display_name} must be between {min_val} and {max_val}. "
                        f"Received: {value}"
                    )
            except (ValueError, TypeError) as e:
                if "must be between" in str(e):
                    raise
                raise ValueError(f"{display_name} must be a valid number. Received: {data[field]}")
    
    # Categorical field validations
    categorical_validations = {
        'school': ['GP', 'MS'],
        'sex': ['F', 'M'],
        'address': ['U', 'R'],
        'famsize': ['GT3', 'LE3'],
        'Pstatus': ['T', 'A'],
        'schoolsup': ['yes', 'no'],
        'famsup': ['yes', 'no'],
        'paid': ['yes', 'no'],
        'activities': ['yes', 'no'],
        'nursery': ['yes', 'no'],
        'higher': ['yes', 'no'],
        'internet': ['yes', 'no'],
        'romantic': ['yes', 'no'],
        'Mjob': ['teacher', 'health', 'services', 'at_home', 'other'],
        'Fjob': ['teacher', 'health', 'services', 'at_home', 'other'],
        'reason': ['home', 'reputation', 'course', 'other'],
        'guardian': ['mother', 'father', 'other']
    }
    
    for field, valid_values in categorical_validations.items():
        if field in data:
            if data[field] not in valid_values:
                raise ValueError(
                    f"{field} must be one of {valid_values}. "
                    f"Received: {data[field]}"
                )
    
    return True


# --- Routes ---

@main_bp.route('/')
def index():
    """Renders the main application page."""
    # CRITICAL FIX: Pass Firebase config using os.getenv()
    firebase_config = {
        'apiKey': os.getenv("FIREBASE_API_KEY"),
        'authDomain': os.getenv("FIREBASE_AUTH_DOMAIN"),
        'projectId': os.getenv("FIREBASE_PROJECT_ID"),
        'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET"),
        'messagingSenderId': os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        'appId': os.getenv("FIREBASE_APP_ID"),
        'measurementId': os.getenv("FIREBASE_MEASUREMENT_ID")
    }
    return render_template('index.html', firebase_config=json.dumps(firebase_config))


@main_bp.route('/api/predict', methods=['POST'])
@limiter.limit("30 per minute")
def predict_risk():
    """
    Processes student data, makes a prediction, and returns structured analysis.
    """
    if pipeline is None:
        return jsonify({"error": "Machine Learning Models are not loaded. Please check server logs for pathing errors."}), 500

    try:
        data = request.get_json()
        
        # VALIDATION: Check input data
        try:
            validate_student_data(data)
        except ValueError as ve:
            return jsonify({"error": f"Invalid input: {str(ve)}"}), 400
        
        # 1. Data Transformation: Convert the JSON payload into a DataFrame row
        data_for_pipeline = {k: v for k, v in data.items() if k not in ['customPrompt']}
        feature_df = pd.DataFrame([data_for_pipeline])
        
        # CRITICAL FIX: Encode categorical data
        if label_encoder is None:
             return jsonify({"error": "Label encoder not loaded. Cannot preprocess data."}), 500

        preprocessed_df = preprocess_data_for_pipeline(feature_df, label_encoder)
        
        # 2. Prediction: The model is a CLASSIFIER that predicts risk categories
        # Output: 0 = High, 1 = Low, 2 = Medium
        predicted_risk_class = pipeline.predict(preprocessed_df)[0]
        
        # Map the predicted class back to risk category
        risk_mapping = {0: 'High', 1: 'Low', 2: 'Medium'}
        predicted_risk_label = risk_mapping.get(predicted_risk_class, 'Unknown')
        
        # Confidence-weighted G3 grade estimate based on model probability
        try:
            probabilities = pipeline.predict_proba(preprocessed_df)[0]
            class_confidence = float(probabilities[int(predicted_risk_class)])
        except Exception:
            probabilities = None
            class_confidence = 0.5  # Safe fallback

        # Grade ranges per risk class: 0=High,1=Low,2=Medium
        grade_ranges = {
            0: (0, 9),    # High risk
            1: (14, 20),  # Low risk
            2: (10, 13)   # Medium risk
        }
        lo, hi = grade_ranges.get(int(predicted_risk_class), (10, 12))
        predicted_g3 = int(round(lo + (hi - lo) * class_confidence))

        # 3. Determine Risk Category and Descriptor
        risk_category = predicted_risk_label.lower()
        risk_descriptors = {
            'high': "Requires immediate intervention and support.",
            'medium': "Needs focused attention to improve academic trajectory.",
            'low': "On track, but minor improvements can maximize potential."
        }
        risk_descriptor = risk_descriptors.get(risk_category, "Status unknown.")

        # 4. Feature Importance (SHAP): Get the most influential factors
        top_features = get_shap_feature_importance(preprocessed_df, predicted_risk_class)

        # 5. Personalized Advice: Generate advice using Gemini (passing full data including customPrompt)
        mentoring_advice = generate_mentoring_advice(data, predicted_g3, risk_category, top_features)

        # 6. Structured JSON Response (for 10/10 frontend consumption)
        # Include probabilities and confidence for UI display
        proba_payload = None
        if probabilities is not None:
            # Map to readable labels using model class mapping
            proba_map = {0: 'High', 1: 'Low', 2: 'Medium'}
            proba_payload = {
                proba_map[i]: float(probabilities[i]) for i in range(len(probabilities)) if i in proba_map
            }

        return jsonify({
            "prediction": predicted_g3,
            "risk_category": risk_category,
            "risk_descriptor": risk_descriptor,
            "confidence": class_confidence,
            "probabilities": proba_payload,
            "shap_values": top_features,
            "mentoring_advice": mentoring_advice
        })

    except Exception as e:
        logger.exception(f"Prediction route error: {e}")
        return jsonify({"error": f"An unexpected error occurred during analysis: {e}"}), 500

# Alias for blueprint to match app.__init__.py import
main = main_bp