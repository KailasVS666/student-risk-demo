import os
import json
import joblib
import numpy as np
import pandas as pd
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import google.generativeai as genai
from dotenv import load_dotenv
import shap
import logging
from .limits import limiter
from .utils import send_faculty_alert  # NEW IMPORT

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

main_bp = Blueprint('main', __name__)

# Pathing Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'early_warning_model_pipeline_tuned.joblib')
SHAP_EXPLAINER_PATH = os.path.join(BASE_DIR, 'student_risk_classifier_tuned.joblib')
LABEL_ENCODER_PATH = os.path.join(BASE_DIR, 'label_encoder.joblib')

# Load Models
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

# Initialize Gemini
gemini_model = None
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("Gemini model initialized successfully.")
    else:
        logger.warning("GEMINI_API_KEY not found.")
except Exception as e:
    logger.error(f"Error initializing Gemini model: {e}")

# --- Helper Functions ---

def preprocess_data_for_pipeline(data_df, label_encoder):
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
                encoded_data_df[col] = encoder_map.transform([raw_value])[0]
            else:
                encoded_data_df[col] = 0 
    
    expected_columns = [
        'school', 'sex', 'age', 'address', 'famsize', 'Pstatus', 'Medu', 'Fedu',
        'Mjob', 'Fjob', 'reason', 'guardian', 'traveltime', 'studytime',
        'failures', 'schoolsup', 'famsup', 'paid', 'activities', 'nursery',
        'higher', 'internet', 'romantic', 'famrel', 'freetime', 'goout',
        'Dalc', 'Walc', 'health', 'absences', 'G1', 'G2', 
        'average_grade', 'grade_change'
    ]
    encoded_data_df = encoded_data_df[expected_columns]
    return encoded_data_df

def map_risk_category(grade):
    if grade < 10:
        return "high", "Requires immediate intervention and support."
    elif 10 <= grade <= 13:
        return "medium", "Needs focused attention to improve academic trajectory."
    else:
        return "low", "On track, but minor improvements can maximize potential."

def get_shap_feature_importance(preprocessed_data, predicted_class):
    if risk_explainer is None:
        return [{'feature': 'G2 Grade', 'importance': 0.85}, {'feature': 'Failures', 'importance': -0.65}]
    try:
        feature_names = preprocessed_data.columns.tolist()
        try:
            explainer = shap.Explainer(risk_explainer)
            exp = explainer(preprocessed_data)
            values = getattr(exp, 'values', None)
        except Exception:
            explainer = shap.TreeExplainer(risk_explainer)
            values = explainer.shap_values(preprocessed_data)

        class_values = None
        if isinstance(values, list):
            class_values = values[int(predicted_class)][0]
        elif hasattr(values, 'ndim'):
            if values.ndim == 3:
                class_values = values[0, int(predicted_class), :]
            elif values.ndim == 2:
                class_values = values[0, :]
            else:
                class_values = values.reshape(values.shape[-1])
        else:
            class_values = np.array(values)[0]

        importance_pairs = list(zip(feature_names, class_values.tolist()))
        top_sorted = sorted(importance_pairs, key=lambda x: abs(x[1]), reverse=True)[:5]
        
        readable_names = {'G1': 'First Grade', 'G2': 'Second Grade', 'failures': 'Past Failures', 'studytime': 'Weekly Study Time', 'absences': 'Absences', 'Medu': "Mother's Edu", 'Fedu': "Father's Edu", 'goout': 'Going Out', 'health': 'Health', 'famrel': 'Family Rel'}
        
        return [{'feature': readable_names.get(name, name), 'importance': float(val)} for name, val in top_sorted]
    except Exception as e:
        logger.exception(f"SHAP error: {e}")
        return [{'feature': 'G2', 'importance': 0.85}, {'feature': 'Failures', 'importance': 0.40}]

# --- ACTION ROUTING LOGIC ---

def get_mentoring_strategy(risk_category):
    strategies = {
        'high': {
            'persona': 'Academic Crisis Counselor',
            'focus': 'Immediate intervention, recovery plans, and fundamental concept review.',
            'routing_action': '🚩 ALERT: Routed to Human Intervention Team',
            'tone': 'Urgent, supportive, and highly structured'
        },
        'medium': {
            'persona': 'Empathetic Study Coach',
            'focus': 'Study habit refinement, time management, and motivation.',
            'routing_action': 'ℹ️ ROUTE: Standard AI Mentoring Session',
            'tone': 'Encouraging, practical, and conversational'
        },
        'low': {
            'persona': 'High-Performance Career Mentor',
            'focus': 'Advanced academic opportunities, leadership, and scholarships.',
            'routing_action': '🚀 ROUTE: Academic Excellence Path',
            'tone': 'Challenging, professional, and growth-oriented'
        }
    }
    return strategies.get(risk_category.lower(), strategies['medium'])

def generate_mentoring_advice(student_data, predicted_g3, risk_category, top_features):
    if gemini_model is None:
        return "Mentoring advice unavailable."

    strategy = get_mentoring_strategy(risk_category)
    feature_list = "\n".join([f"* **{f['feature']}**: Impact {f['importance']:.2f}" for f in top_features])
    custom_prompt_text = student_data.get('customPrompt', '').strip()
    custom_prompt_section = f"User Request: '{custom_prompt_text}'" if custom_prompt_text else ""

    prompt = f"""
    ROLE: You are an {strategy['persona']}.
    STRATEGY: {strategy['focus']}
    TONE: {strategy['tone']}
    
    CONTEXT:
    {custom_prompt_section}
    - Predicted Final Grade: {predicted_g3} / 20
    - Risk Level: {risk_category.upper()}
    - Key Factors:
    {feature_list}

    TASK: Provide advice in 3 sections (### headings) with max 4 bullets each.
    
    ### ⚡ Priority Actions
    (Advice specific to the {strategy['persona']})
    
    ### 📚 Academic Plan
    
    ### 🧘 Personal Growth
    """

    try:
        response = gemini_model.generate_content(prompt)
        advice_text = getattr(response, 'text', '').strip() or "No advice generated."
        return f"> **{strategy['routing_action']}**\n\n{advice_text}"
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return f"Error generating advice: {e}"

def validate_student_data(data):
    required = ['G1', 'G2', 'age', 'school', 'sex']
    for field in required:
        if field not in data: raise ValueError(f"Missing: {field}")
    return True

# --- Routes ---

@main_bp.route('/')
def index():
    return redirect('/login')

@main_bp.route('/api/predict', methods=['POST'])
@limiter.limit("30 per minute")
def predict_risk():
    if pipeline is None:
        return jsonify({"error": "Models not loaded."}), 500

    try:
        data = request.get_json()
        validate_student_data(data)
        
        # 1. Transform & Predict
        data_for_pipeline = {k: v for k, v in data.items() if k not in ['customPrompt']}
        feature_df = pd.DataFrame([data_for_pipeline])
        
        if label_encoder is None: return jsonify({"error": "Label encoder not loaded."}), 500
        preprocessed_df = preprocess_data_for_pipeline(feature_df, label_encoder)
        
        predicted_risk_class = pipeline.predict(preprocessed_df)[0]
        risk_mapping = {0: 'High', 1: 'Low', 2: 'Medium'}
        risk_category = risk_mapping.get(predicted_risk_class, 'Unknown').lower()
        
        # 2. Grade & Confidence
        try:
            probabilities = pipeline.predict_proba(preprocessed_df)[0]
            class_confidence = float(probabilities[int(predicted_risk_class)])
        except:
            probabilities = None
            class_confidence = 0.5
            
        grade_ranges = {0: (0, 9), 1: (14, 20), 2: (10, 13)}
        lo, hi = grade_ranges.get(int(predicted_risk_class), (10, 12))
        predicted_g3 = int(round(lo + (hi - lo) * class_confidence))
        risk_descriptor = map_risk_category(predicted_g3)[1]

        # 3. ACTION ROUTER: Trigger Alert if High Risk
        if risk_category == 'high':
            # This is the "Device" functionality triggering real-world action
            send_faculty_alert(data, risk_category, predicted_g3)

        # 4. Generate AI Advice
        top_features = get_shap_feature_importance(preprocessed_df, predicted_risk_class)
        mentoring_advice = generate_mentoring_advice(data, predicted_g3, risk_category, top_features)

        # 5. Response
        proba_payload = None
        if probabilities is not None:
            proba_map = {0: 'High', 1: 'Low', 2: 'Medium'}
            proba_payload = {proba_map[i]: float(probabilities[i]) for i in range(len(probabilities)) if i in proba_map}

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
        logger.exception(f"Prediction error: {e}")
        return jsonify({"error": f"Error: {e}"}), 500

main = main_bp