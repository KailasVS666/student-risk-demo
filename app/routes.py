from flask import Blueprint, request, jsonify, render_template, current_app
import pandas as pd
import shap
import json
import numpy as np
import google.generativeai as genai
import traceback

# Create a Blueprint
main_bp = Blueprint('main', __name__)

# --- NEW: Helper function to build a detailed, context-rich prompt ---
def build_gemini_prompt(student_data, custom_prompt=""):
    """
    Creates a detailed, structured prompt for the Gemini API by translating
    student data into human-readable context.
    """
    # --- Data Dictionaries for Translation ---
    education_levels = {0: "None", 1: "Primary (4th grade)", 2: "5th to 9th grade", 3: "Secondary", 4: "Higher education"}
    job_types = {"teacher": "Teacher", "health": "Health care", "services": "Civil services", "at_home": "At home", "other": "Other"}
    yes_no = {"yes": "Yes", "no": "No"}

    # --- Build a human-readable context string ---
    context = f"""
    ### Student Context
    - **Demographics:** Age {student_data.get('age')}. Lives in an '{student_data.get('address', 'N/A').upper()}' (Urban/Rural) area.
    - **Family Background:**
        - Mother's Education: {education_levels.get(student_data.get('Medu'), 'N/A')}.
        - Father's Education: {education_levels.get(student_data.get('Fedu'), 'N/A')}.
        - Mother's Job: {job_types.get(student_data.get('Mjob'), 'N/A')}.
        - Father's Job: {job_types.get(student_data.get('Fjob'), 'N/A')}.
        - Family Relationship Quality: {student_data.get('famrel')}/5.
    - **Academic Profile:**
        - Recent Grades (G1, G2): {student_data.get('G1')}/20, {student_data.get('G2')}/20.
        - Past Failures: {student_data.get('failures')}.
        - Weekly Study Time: {student_data.get('studytime')} (1: <2 hrs, 2: 2-5 hrs, 3: 5-10 hrs, 4: >10 hrs).
        - Wants to pursue higher education: {yes_no.get(student_data.get('higher'), 'N/A')}.
    - **Social & Lifestyle:**
        - Goes out with friends: {student_data.get('goout')}/5 (Frequency).
        - In a romantic relationship: {yes_no.get(student_data.get('romantic'), 'N/A')}.
        - Weekday & Weekend Alcohol Consumption: {student_data.get('Dalc')}/5 and {student_data.get('Walc')}/5.
    """

    # --- Construct the full prompt ---
    prompt = f"""
    **Persona:** You are an expert, empathetic, and highly motivational student mentor. Your tone should be encouraging, insightful, and constructive. Avoid being generic; use the specific details from the student's context to make your advice personal and actionable.

    **Task:** Based on the student's profile below, provide personalized mentoring advice. Structure your response in Markdown using the following strict format:
    ### 1. Overall Assessment
    ### 2. Key Strengths to Celebrate
    ### 3. Areas for Strategic Focus
    ### 4. Actionable Steps & Strategies
    ### 5. Recommended Resources

    {context}
    """
    
    if custom_prompt:
        prompt += f"\n**Additional Guidance:** Please also address the user's specific request: '{custom_prompt}'"
    
    return prompt

def preprocess_student_data(data):
    """
    Takes raw student data, converts it to a DataFrame, and engineers new features.
    """
    df = pd.DataFrame([data])
    df['grade_change'] = df['G2'] - df['G1']
    df['average_grade'] = (df['G1'] + df['G2']) / 2
    return df

@main_bp.route('/')
def home():
    """Serves the main HTML file."""
    return render_template('index.html')

@main_bp.route('/firebase-config')
def firebase_config():
    """Provides the Firebase configuration to the frontend."""
    return jsonify(current_app.config['FIREBASE_CONFIG'])

@main_bp.route('/predict-risk', methods=['POST'])
def predict_risk():
    """Predicts student risk level."""
    try:
        model_pipeline = current_app.config['MODEL_PIPELINE']
        label_encoder = current_app.config['LABEL_ENCODER']
        data = request.json.get('student_data')
        if not data:
            return jsonify({"error": "No student data provided."}), 400

        input_df = preprocess_student_data(data)
        prediction_encoded = model_pipeline.predict(input_df)
        risk_label = label_encoder.inverse_transform(prediction_encoded)
        return jsonify({'risk_level': risk_label[0]})
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({"error": "Failed to make a prediction."}), 500

@main_bp.route('/explain-prediction', methods=['POST'])
def explain_prediction():
    """Provides a SHAP-based explanation for a prediction."""
    try:
        model_pipeline = current_app.config['MODEL_PIPELINE']
        core_model = current_app.config['CORE_MODEL']
        label_encoder = current_app.config['LABEL_ENCODER']
        data = request.json.get('student_data')
        if not data:
            return jsonify({"error": "No student data provided."}), 400
            
        input_df = preprocess_student_data(data)
        preprocessor = model_pipeline.named_steps['preprocessor']
        processed_data = preprocessor.transform(input_df)
        
        explainer = shap.TreeExplainer(core_model)
        shap_values = explainer.shap_values(processed_data)
        
        high_risk_index = list(label_encoder.classes_).index('High')
        instance_shap = shap_values[high_risk_index][0]
        
        feature_names = preprocessor.get_feature_names_out()
        feature_importance = sorted(zip(feature_names, instance_shap), key=lambda x: abs(x[1]), reverse=True)
        return jsonify({"explanation": feature_importance[:10]})
    except Exception as e:
        print(f"SHAP explanation error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to generate explanation."}), 500

# --- UPDATED: Route using the new prompt builder ---
@main_bp.route('/generate-advice', methods=['POST'])
def generate_advice_endpoint():
    """Connects to the Gemini API to generate personalized advice."""
    try:
        gemini_api_key = current_app.config['GEMINI_API_KEY']
        data = request.json.get('student_data')
        custom_prompt_text = data.pop('custom_prompt', '')

        if not data:
            return jsonify({"error": "No student data provided"}), 400

        # Use the new helper function to build the prompt
        prompt = build_gemini_prompt(data, custom_prompt_text)
        
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-pro-latest')
        response = model.generate_content(prompt)
        
        return jsonify({"advice": response.text})

    except Exception as e:
        print("--- DETAILED GEMINI API ERROR ---")
        traceback.print_exc()
        return jsonify({"error": "Failed to connect to the AI service."}), 500

@main_bp.route('/get-grade-averages', methods=['GET'])
def get_grade_averages():
    """Retrieves pre-calculated grade averages."""
    try:
        grades_avg = current_app.config.get('GRADE_AVERAGES')
        if grades_avg is None:
            return jsonify({"error": "Grade averages not found."}), 500
        return jsonify(grades_avg)
    except Exception as e:
        print(f"Error fetching grade averages: {e}")
        return jsonify({"error": "Failed to retrieve grade averages."}), 500