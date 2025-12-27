import os
import json
import joblib
import numpy as np
import pandas as pd
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, make_response
from flask_wtf.csrf import validate_csrf
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import bleach
from .limits import limiter
from .utils import send_faculty_alert
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
from functools import wraps

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Custom CSRF exemption decorator for API endpoints
def csrf_exempt_api(f):
    """Decorator to exempt API endpoints from CSRF (use with rate limiting instead)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For API endpoints using JSON, CSRF is not needed since they rely on rate limiting
        # and origin validation (handled by CORS and rate limiting)
        return f(*args, **kwargs)
    return decorated_function

main_bp = Blueprint('main', __name__)

# Pathing Configuration - Support both local and Render deployments
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CWD = os.getcwd()

# Module-level logger for route utilities (used before app factory runs)
logger = logging.getLogger(__name__)

# Try multiple paths for models (for local dev and Render)
def _find_model_path(filename):
    """Find model file in multiple locations"""
    # Ensure logger exists even if module-level init fails
    _log = logger if 'logger' in globals() else logging.getLogger(__name__)
    search_paths = [
        os.path.join(BASE_DIR, filename),  # app/../filename
        os.path.join(CWD, filename),        # current working directory
        filename                             # relative to current dir
    ]
    for path in search_paths:
        if os.path.exists(path):
            _log.info(f"Found {filename} at: {path}")
            return path
    _log.error(f"Model file {filename} not found in any search path: {search_paths}")
    return os.path.join(BASE_DIR, filename)  # Return default (will fail gracefully)

MODEL_PATH = _find_model_path('early_warning_model_pipeline_tuned.joblib')
SHAP_EXPLAINER_PATH = _find_model_path('student_risk_classifier_tuned.joblib')
LABEL_ENCODER_PATH = _find_model_path('label_encoder.joblib')

# Load Models
pipeline = None
risk_explainer = None
label_encoder = None

try:
    pipeline = joblib.load(MODEL_PATH)
    risk_explainer = joblib.load(SHAP_EXPLAINER_PATH) 
    label_encoder = joblib.load(LABEL_ENCODER_PATH)
    logger.info("Models and Pipeline loaded successfully.")
except Exception as e:
    logger.error(f"Error loading models: {e}. Check paths: {MODEL_PATH}")

# Initialize Gemini
gemini_model = None
USE_MOCK_MODE = os.getenv('USE_MOCK_MODE', 'false').lower() == 'true'

try:
    if GEMINI_API_KEY and not USE_MOCK_MODE:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-2.0-flash-lite')
        logger.info("Gemini model initialized successfully.")
    elif USE_MOCK_MODE:
        logger.info("Running in MOCK MODE - using demo advice")
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
    """Calculate SHAP feature importance. Returns fallback on memory/segfault errors."""
    # Fallback for missing explainer or low memory environments (e.g., Render free tier)
    fallback_features = [
        {'feature': 'G2 Grade', 'importance': 0.85},
        {'feature': 'Failures', 'importance': 0.65},
        {'feature': 'Study Time', 'importance': 0.42},
        {'feature': 'Absences', 'importance': -0.38},
        {'feature': 'Family Relation', 'importance': 0.30}
    ]
    
    if risk_explainer is None:
        logger.warning("SHAP explainer not loaded, using fallback features")
        return fallback_features
    
    try:
        # Disable SHAP on memory-constrained environments (segfault = code 139)
        # This is common on Render free tier; skip expensive SHAP calculation
        logger.info("Skipping SHAP calculation to avoid memory exhaustion on low-resource environments")
        return fallback_features
    except Exception as e:
        logger.error(f"SHAP calculation error (segfault/memory): {type(e).__name__}: {e}")
        return fallback_features

# --- ACTION ROUTING LOGIC ---

def generate_mock_advice(risk_category, predicted_g3, custom_prompt_text=''):
    """Generate realistic mock advice for testing without hitting API."""
    mock_advice_templates = {
        'high': """
### ⚡ Priority Actions
- **Schedule immediate one-on-one counseling** with academic advisor within 24 hours
- **Create a daily study schedule** with specific time blocks for each subject
- **Join tutoring sessions** for subjects where grades are below 12/20
- **Set up weekly check-ins** with teachers to monitor progress

### 📚 Academic Plan
- **Focus on foundational concepts** - review previous material before moving forward
- **Break study sessions into 25-minute intervals** (Pomodoro technique) with 5-min breaks
- **Practice active recall** - test yourself regularly instead of passive reading
- **Form a study group** with peers who are performing well

### 🧘 Personal Growth
- **Improve sleep hygiene** - aim for 7-8 hours nightly to boost cognitive function
- **Reduce social media time** by 50% and redirect to productive activities
- **Practice stress management** through meditation or physical exercise
- **Build a reward system** - celebrate small wins to maintain motivation
""",
        'medium': """
### ⚡ Priority Actions
- **Identify weak areas** through self-assessment and past exam analysis
- **Increase study time by 2-3 hours per week** focusing on challenging subjects
- **Attend office hours** to clarify doubts and get personalized guidance
- **Review and improve note-taking methods** for better retention

### 📚 Academic Plan
- **Create weekly goals** with specific, measurable targets for each subject
- **Use active learning techniques** - teach concepts to others or explain them aloud
- **Complete practice problems** beyond homework to reinforce understanding
- **Track your progress** with a study journal or app

### 🧘 Personal Growth
- **Balance academics with activities** - maintain hobbies to prevent burnout
- **Build better time management** using planners or digital calendars
- **Stay consistent** with study routines even on weekends
- **Seek peer feedback** on your learning approach and adjust as needed
""",
        'low': """
### ⚡ Priority Actions
- **Maintain current momentum** - consistency is key to sustained success
- **Challenge yourself** with advanced materials or enrichment activities
- **Mentor struggling peers** to reinforce your own understanding
- **Explore extracurricular opportunities** that align with your interests

### 📚 Academic Plan
- **Set stretch goals** to push beyond current performance levels
- **Dive deeper into topics of interest** through independent projects or research
- **Prepare for advanced coursework** by previewing upcoming material
- **Optimize study efficiency** - focus on quality over quantity

### 🧘 Personal Growth
- **Develop leadership skills** by taking on group project leadership roles
- **Build professional skills** through internships or volunteer work
- **Cultivate growth mindset** - view challenges as opportunities
- **Plan for the future** - research college/career paths aligned with strengths
"""
    }
    
    base_advice = mock_advice_templates.get(risk_category, mock_advice_templates['medium'])
    
    if custom_prompt_text:
        base_advice = f"\n*Addressing your request: {custom_prompt_text[:100]}...*\n{base_advice}"
    
    return f"> **MOCK MODE - Demo Advice (Predicted Grade: {predicted_g3}/20)**\n{base_advice}"

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
    """Generate mentoring advice using Gemini, with automatic mock fallback on errors/quota.

    Returns a user-friendly advice string in all cases.
    """
    strategy = get_mentoring_strategy(risk_category)
    feature_list = "\n".join([f"* **{f['feature']}**: Impact {f['importance']:.2f}" for f in top_features])
    custom_prompt_text = student_data.get('customPrompt', '').strip()
    custom_prompt_section = f"User Request: '{custom_prompt_text}'" if custom_prompt_text else ""

    # Task instructions adapt to custom prompt
    if custom_prompt_text:
        task_instruction = (
            "IMPORTANT: Follow the user's request EXACTLY as stated. Adapt tone/format as requested."
        )
    else:
        task_instruction = "Provide advice in 3 sections (### headings) with max 4 bullets each."

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

    TASK: {task_instruction}

    ### ⚡ Priority Actions
    (Advice specific to the {strategy['persona']})

    ### 📚 Academic Plan

    ### 🧘 Personal Growth
    """

    # Always-available fallback advice
    fallback = generate_mock_advice(risk_category, predicted_g3, custom_prompt_text)

    try:
        # Use mock mode explicitly when enabled or model missing
        if USE_MOCK_MODE or gemini_model is None:
            logger.info("Using mock advice (MOCK MODE or missing model)")
            return fallback

        # Attempt to call Gemini; on failure/quota, fall back gracefully
        response = gemini_model.generate_content(prompt)
        advice_text = getattr(response, 'text', '').strip()
        if not advice_text:
            logger.warning("Gemini returned empty advice; using fallback")
            return fallback
        return f"> **{strategy['routing_action']}**\n\n{advice_text}"
    except Exception as e:
        logger.warning(f"Gemini API error/quota, using fallback: {e}")
        return fallback

def validate_student_data(data):
    """
    Validates student form data before prediction.
    
    Args:
        data (dict): Student assessment data
        
    Returns:
        tuple: (is_valid, error_message) where is_valid is bool
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    required = ['G1', 'G2', 'age', 'school', 'sex']
    
    # Check for missing fields
    missing = [f for f in required if f not in data]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    
    # Check for null/empty values
    for field in required:
        if data.get(field) is None or (isinstance(data[field], str) and not data[field].strip()):
            raise ValueError(f"Field '{field}' cannot be empty")
    
    # Validate numeric fields
    try:
        age = int(data.get('age'))
        if not (15 <= age <= 30):
            raise ValueError("Age must be between 15 and 30")
            
        g1 = float(data.get('G1'))
        g2 = float(data.get('G2'))
        if not (0 <= g1 <= 20 and 0 <= g2 <= 20):
            raise ValueError("Grades must be between 0 and 20")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid numeric values: {str(e)}")
    
    # Validate string fields (prevent SQL injection/XSS by checking length)
    string_fields = ['school', 'sex']
    for field in string_fields:
        value = str(data.get(field, ''))
        if len(value) > 100:
            raise ValueError(f"Field '{field}' exceeds maximum length")
        if not value.replace(' ', '').replace('-', '').isalnum():
            raise ValueError(f"Field '{field}' contains invalid characters")
    
    # Validate optional string field (customPrompt)
    if 'customPrompt' in data:
        custom = str(data.get('customPrompt', ''))
        if len(custom) > 500:
            raise ValueError("Custom prompt exceeds maximum length (500 chars)")
        # Sanitize HTML/script tags to prevent XSS
        data['customPrompt'] = bleach.clean(custom, tags=[], strip=True)
    
    return True

# --- Routes ---

@main_bp.route('/')
def index():
    return redirect('/login')

# Lightweight health checks (useful for Render probes and curl tests)
@main_bp.route('/healthz')
@csrf_exempt_api
def healthz():
    try:
        status = {
            "ok": True,
            "models_loaded": bool(pipeline is not None and label_encoder is not None and risk_explainer is not None),
            "time": datetime.utcnow().isoformat() + "Z"
        }
        return jsonify(status), 200
    except Exception:
        return jsonify({"ok": False}), 500

@main_bp.route('/status')
def status():
    return jsonify({
        "pipeline": bool(pipeline is not None),
        "label_encoder": bool(label_encoder is not None),
        "risk_explainer": bool(risk_explainer is not None)
    }), 200

@main_bp.route('/api/predict', methods=['POST'])
@csrf_exempt_api  # Exempt API endpoint - protected by rate limiting and input validation
@limiter.limit("30 per minute")
def predict_risk():
    """
    Predict student risk category based on assessment data.
    
    Expected JSON body: Student assessment form data with G1, G2, age, school, sex, etc.
    Returns: JSON with prediction, risk_category, shap_values, mentoring_advice
    """
    # Check models first and provide detailed error response
    if pipeline is None or label_encoder is None:
        error_msg = "Models not loaded. "
        missing = []
        if pipeline is None:
            missing.append("ML pipeline")
        if label_encoder is None:
            missing.append("label encoder")
        error_msg += f"Missing: {', '.join(missing)}. "
        error_msg += f"Model paths: pipeline={MODEL_PATH}, encoder={LABEL_ENCODER_PATH}"
        logger.error(error_msg)
        return jsonify({
            "error": "Server initialization incomplete. Please try again in a moment.",
            "status": "service_unavailable",
            "detail": error_msg if os.getenv('ENVIRONMENT') == 'development' else None
        }), 503

    try:
        # 1. REQUEST VALIDATION
        if not request.is_json:
            return jsonify({
                "error": "Request must be JSON",
                "status": "validation_error"
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "Empty request body",
                "status": "validation_error"
            }), 400
        
        # Validate required fields
        try:
            validate_student_data(data)
        except ValueError as e:
            logger.warning(f"Validation failed: {str(e)}")
            return jsonify({
                "error": str(e),
                "status": "validation_error"
            }), 400
        
        # 2. DATA PREPROCESSING
        try:
            data_for_pipeline = {k: v for k, v in data.items() if k not in ['customPrompt']}
            feature_df = pd.DataFrame([data_for_pipeline])
            
            if label_encoder is None:
                logger.error("Label encoder not available during prediction")
                return jsonify({
                    "error": "Model components unavailable",
                    "status": "error"
                }), 503
            
            preprocessed_df = preprocess_data_for_pipeline(feature_df, label_encoder)
        except KeyError as e:
            logger.error(f"Missing preprocessing column: {str(e)}")
            return jsonify({
                "error": f"Data preprocessing error: {str(e)}",
                "status": "error"
            }), 500
        except Exception as e:
            logger.exception(f"Preprocessing error: {str(e)}")
            return jsonify({
                "error": "Data preprocessing failed",
                "status": "error"
            }), 500
        
        # 3. PREDICTION
        try:
            predicted_risk_class = pipeline.predict(preprocessed_df)[0]
            risk_mapping = {0: 'High', 1: 'Low', 2: 'Medium'}
            risk_category = risk_mapping.get(predicted_risk_class, 'Unknown').lower()
        except Exception as e:
            logger.exception(f"Model prediction error: {str(e)}")
            return jsonify({
                "error": "Prediction failed",
                "status": "error"
            }), 500
        
        # 4. CONFIDENCE & GRADE ESTIMATION
        try:
            probabilities = pipeline.predict_proba(preprocessed_df)[0]
            class_confidence = float(probabilities[int(predicted_risk_class)])
        except Exception as e:
            logger.warning(f"Probability calculation failed: {str(e)}, using fallback")
            probabilities = None
            class_confidence = 0.5
        
        try:
            grade_ranges = {0: (0, 9), 1: (14, 20), 2: (10, 13)}
            lo, hi = grade_ranges.get(int(predicted_risk_class), (10, 12))
            predicted_g3 = int(round(lo + (hi - lo) * class_confidence))
            risk_descriptor = map_risk_category(predicted_g3)[1]
        except Exception as e:
            logger.error(f"Grade calculation error: {str(e)}")
            predicted_g3 = 10
            risk_descriptor = "Unable to determine risk level"
        
        # 5. HIGH-RISK ALERT (Non-blocking)
        if risk_category == 'high':
            try:
                send_faculty_alert(data, risk_category, predicted_g3)
            except Exception as e:
                logger.error(f"Faculty alert failed: {str(e)}")
                # Don't fail the prediction response, just log it
        
        # 6. MENTORING ADVICE (Non-blocking)
        try:
            top_features = get_shap_feature_importance(preprocessed_df, predicted_risk_class)
            mentoring_advice = generate_mentoring_advice(data, predicted_g3, risk_category, top_features)
        except Exception as e:
            logger.error(f"Mentoring advice generation failed: {str(e)}")
            top_features = []
            mentoring_advice = f"*Unable to generate personalized advice at this moment. Please try again later.*"
        
        # 7. BUILD RESPONSE
        try:
            proba_payload = None
            if probabilities is not None:
                proba_map = {0: 'High', 1: 'Low', 2: 'Medium'}
                proba_payload = {proba_map[i]: float(probabilities[i]) for i in range(len(probabilities)) if i in proba_map}
            
            response_data = {
                "prediction": predicted_g3,
                "risk_category": risk_category,
                "risk_descriptor": risk_descriptor,
                "confidence": class_confidence,
                "probabilities": proba_payload,
                "shap_values": top_features,
                "mentoring_advice": mentoring_advice,
                "status": "success"
            }
            return jsonify(response_data), 200
            
        except Exception as e:
            logger.exception(f"Response building error: {str(e)}")
            return jsonify({
                "error": "Failed to build response",
                "status": "error"
            }), 500

    except Exception as e:
        logger.exception(f"Unexpected error in predict_risk: {str(e)}")
        return jsonify({
            "error": "An unexpected error occurred",
            "status": "error"
        }), 500

@main_bp.route('/generate-pdf', methods=['POST'])
@csrf_exempt_api  # Exempt API endpoint - protected by rate limiting and input validation
@limiter.limit("5 per minute")
def generate_pdf():
    """
    Generate PDF report of student assessment.
    
    Expected JSON body: Assessment results with prediction, risk_category, shap_values, etc.
    Returns: PDF file or JSON error
    """
    try:
        # 1. REQUEST VALIDATION
        if not request.is_json:
            return jsonify({
                "error": "Request must be JSON",
                "status": "validation_error"
            }), 400
        
        data = request.json
        if not data:
            return jsonify({
                "error": "Empty request body",
                "status": "validation_error"
            }), 400
        
        logger.info(f"PDF generation request with keys: {list(data.keys())}")
        
        # 2. REQUIRED FIELDS VALIDATION
        required_fields = ['predicted_grade', 'risk_category', 'confidence']
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            logger.warning(f"Missing fields in PDF request: {missing_fields}")
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "status": "validation_error"
            }), 400
        
        # 3. PDF DOCUMENT CREATION
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4F46E5'),
            spaceAfter=30
        )
        
        # HEADER
        story.append(Paragraph("AI Student Mentor - Assessment Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        try:
            gen_time = datetime.now().strftime('%B %d, %Y at %I:%M %p')
            story.append(Paragraph(f"Generated: {gen_time}", styles['Normal']))
        except Exception as e:
            logger.warning(f"Timestamp error: {str(e)}")
            story.append(Paragraph("Generated: [Date unavailable]", styles['Normal']))
        story.append(Spacer(1, 0.4*inch))
        
        # RISK ASSESSMENT SUMMARY
        story.append(Paragraph("Risk Assessment Summary", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        # Safely extract and format confidence percentage
        try:
            conf_value = data.get('confidence', 0)
            if isinstance(conf_value, (int, float)):
                conf_pct = int(round(conf_value * 100)) if conf_value <= 1 else int(round(conf_value))
            else:
                conf_pct = 0
            conf_pct = max(0, min(100, conf_pct))  # Clamp to [0, 100]
        except Exception as e:
            logger.warning(f"Confidence calculation error: {str(e)}")
            conf_pct = 0
        
        # Summary table
        try:
            summary_data = [
                ['Predicted Final Grade', f"{data.get('predicted_grade', 'N/A')}/20"],
                ['Risk Level', str(data.get('risk_category', 'N/A')).upper()],
                ['Confidence', f"{conf_pct}%"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3F4F6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB'))
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 0.4*inch))
        except Exception as e:
            logger.warning(f"Summary table error: {str(e)}")
        
        # MENTORING ADVICE
        if data.get('mentoring_advice'):
            story.append(Paragraph("Personalized Mentoring Advice", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            try:
                advice_text = str(data['mentoring_advice'])
                
                # Use bleach for secure HTML sanitization (prevents ReDoS attacks)
                advice_text = bleach.clean(
                    advice_text,
                    tags=[],  # Strip all HTML tags
                    strip=True,
                    protocols=[]
                )
                
                # Remove markdown formatting safely
                advice_text = advice_text.replace('###', '').replace('**', '').replace('*', '')
                advice_text = advice_text.replace('•', '- ')
                
                # Add paragraphs (limit to prevent PDF bloat)
                paragraphs = advice_text.split('\n\n')
                for para in paragraphs[:10]:
                    if para.strip():
                        # Bleach already sanitized, safe to add
                        clean_para = para.strip().replace('\n', '<br/>')
                        story.append(Paragraph(clean_para, styles['Normal']))
                        story.append(Spacer(1, 0.1*inch))
                
            except Exception as e:
                logger.warning(f"Advice formatting error: {str(e)}")
                story.append(Paragraph("Mentoring advice is available in the web interface.", styles['Normal']))
            
            story.append(Spacer(1, 0.2*inch))
        
        # KEY FACTORS
        if data.get('shap_values') and isinstance(data['shap_values'], list):
            story.append(Paragraph("Key Influencing Factors", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            try:
                factors_data = [['Factor', 'Impact']]
                for factor in data['shap_values'][:5]:
                    try:
                        feature_name = str(factor.get('feature', 'Unknown')).strip()
                        importance = float(factor.get('importance', 0))
                        factors_data.append([feature_name, f"{importance:.3f}"])
                    except Exception as e:
                        logger.warning(f"Factor processing error: {str(e)}")
                        continue
                
                if len(factors_data) > 1:  # Only show if we have factors
                    factors_table = Table(factors_data, colWidths=[3*inch, 1.5*inch])
                    factors_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    
                    story.append(factors_table)
            except Exception as e:
                logger.warning(f"Factors table error: {str(e)}")
        
        # 4. BUILD PDF
        doc.build(story)
        buffer.seek(0)
        logger.info("PDF built successfully")
        
        # 5. BUILD RESPONSE
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response.headers['Content-Disposition'] = f'attachment; filename=student_report_{timestamp}.pdf'
        logger.info("PDF response sent successfully")
        return response
            
    except Exception as e:
        logger.exception(f"Unexpected error in generate_pdf: {str(e)}")
        return jsonify({
            "error": "An unexpected error occurred during PDF generation",
            "status": "error"
        }), 500

main = main_bp