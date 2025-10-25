import os
import json
import joblib
import numpy as np
import pandas as pd
from flask import Blueprint, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv

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
try:
    pipeline = joblib.load(MODEL_PATH)
    risk_explainer = joblib.load(SHAP_EXPLAINER_PATH) 
    label_encoder = joblib.load(LABEL_ENCODER_PATH)
    print("Models and Pipeline loaded successfully.")
except Exception as e:
    print(f"Error loading models: {e}. Check paths: {MODEL_PATH}")

# Initialize Gemini Model (google-generativeai SDK)
gemini_model = None
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        # Use gemini-2.5-flash - fast, stable, and widely available
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        print("Gemini model initialized successfully (gemini-2.5-flash).")
    else:
        print("WARNING: GEMINI_API_KEY not found in environment.")
except Exception as e:
    print(f"Error initializing Gemini model: {e}")


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

def get_shap_feature_importance(data):
    """
    Calculates and processes SHAP feature importances.
    *** STATIC PLACEHOLDER DATA FOR UI/UX TESTING ***
    """
    if risk_explainer is None:
        return [
             {'feature': 'G2 (Second Grade)', 'importance': 1.0},
             {'feature': 'Model Error', 'importance': -0.7},
             {'feature': 'Model Error', 'importance': 0.6},
             {'feature': 'Model Error', 'importance': -0.5},
             {'feature': 'Model Error', 'importance': 0.4},
        ]

    top_features = [
        {'feature': 'G2 (Second Grade)', 'importance': 0.85},
        {'feature': 'Failures (Past)', 'importance': -0.65},
        {'feature': 'Study Time', 'importance': 0.40},
        {'feature': 'Absences', 'importance': -0.30},
        {'feature': "Mother's Education", 'importance': 0.25},
    ]

    top_features.sort(key=lambda x: abs(x['importance']), reverse=True)
    return top_features


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
def predict_risk():
    """
    Processes student data, makes a prediction, and returns structured analysis.
    """
    if pipeline is None:
        return jsonify({"error": "Machine Learning Models are not loaded. Please check server logs for pathing errors."}), 500

    try:
        data = request.get_json()
        
        # 1. Data Transformation: Convert the JSON payload into a DataFrame row
        data_for_pipeline = {k: v for k, v in data.items() if k not in ['customPrompt']}
        feature_df = pd.DataFrame([data_for_pipeline])
        
        # CRITICAL FIX: Encode categorical data
        if label_encoder is None:
             return jsonify({"error": "Label encoder not loaded. Cannot preprocess data."}), 500

        preprocessed_df = preprocess_data_for_pipeline(feature_df, label_encoder)
        
        # DEBUG: Check what data looks like after preprocessing
        print(f"\nDEBUG - Before preprocessing:")
        print(f"  G1={feature_df['G1'].iloc[0]}, G2={feature_df['G2'].iloc[0]}, average_grade={feature_df['average_grade'].iloc[0]}")
        print(f"  school={feature_df['school'].iloc[0]}, sex={feature_df['sex'].iloc[0]}")
        print(f"\nDEBUG - After preprocessing:")
        print(f"  G1={preprocessed_df['G1'].iloc[0]}, G2={preprocessed_df['G2'].iloc[0]}, average_grade={preprocessed_df['average_grade'].iloc[0]}")
        print(f"  school={preprocessed_df['school'].iloc[0]}, sex={preprocessed_df['sex'].iloc[0]}")
        print(f"  DataFrame shape: {preprocessed_df.shape}")
        print(f"  Column order: {list(preprocessed_df.columns)[:10]}")
        
        # 2. Prediction: The model is a CLASSIFIER that predicts risk categories
        # Output: 0 = High, 1 = Low, 2 = Medium
        predicted_risk_class = pipeline.predict(preprocessed_df)[0]
        
        # Map the predicted class back to risk category
        risk_mapping = {0: 'High', 1: 'Low', 2: 'Medium'}
        predicted_risk_label = risk_mapping.get(predicted_risk_class, 'Unknown')
        
        # For display purposes, estimate a G3 grade based on risk category
        # This is a rough approximation for the UI
        grade_estimates = {'High': 8, 'Medium': 12, 'Low': 16}
        predicted_g3 = grade_estimates.get(predicted_risk_label, 10)
        
        # DEBUG: Log the actual prediction
        print(f"\nDEBUG: Model predicted class {predicted_risk_class} = {predicted_risk_label} risk")
        print(f"       Input G1={data_for_pipeline.get('G1')}, G2={data_for_pipeline.get('G2')}")
        print(f"       Estimated G3 for display: {predicted_g3}\n")

        # 3. Determine Risk Category and Descriptor
        risk_category = predicted_risk_label.lower()
        risk_descriptors = {
            'high': "Requires immediate intervention and support.",
            'medium': "Needs focused attention to improve academic trajectory.",
            'low': "On track, but minor improvements can maximize potential."
        }
        risk_descriptor = risk_descriptors.get(risk_category, "Status unknown.")

        # 4. Feature Importance (SHAP): Get the most influential factors
        top_features = get_shap_feature_importance(data_for_pipeline)

        # 5. Personalized Advice: Generate advice using Gemini (passing full data including customPrompt)
        mentoring_advice = generate_mentoring_advice(data, predicted_g3, risk_category, top_features)

        # 6. Structured JSON Response (for 10/10 frontend consumption)
        return jsonify({
            "prediction": predicted_g3,
            "risk_category": risk_category, 
            "risk_descriptor": risk_descriptor,
            "shap_values": top_features, 
            "mentoring_advice": mentoring_advice
        })

    except Exception as e:
        print(f"Prediction route error: {e}")
        return jsonify({"error": f"An unexpected error occurred during analysis: {e}"}), 500

# Alias for blueprint to match app.__init__.py import
main = main_bp