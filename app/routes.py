from flask import Blueprint, request, jsonify, render_template, current_app
import pandas as pd
import shap
import requests
import json

# Create a Blueprint object
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Serves the main HTML file."""
    return render_template('index.html')

@main_bp.route('/firebase-config')
def firebase_config():
    """Serves the Firebase configuration."""
    return jsonify(current_app.config['FIREBASE_CONFIG'])

@main_bp.route('/predict-risk', methods=['POST'])
def predict_risk():
    try:
        model_pipeline = current_app.config['MODEL_PIPELINE']
        data = request.json.get('student_data')
        input_df = pd.DataFrame([data])
        prediction = model_pipeline.predict(input_df)
        risk_label = prediction[0]
        return jsonify({'risk_level': risk_label})
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({"error": "Failed to make a prediction."}), 500

@main_bp.route('/explain-prediction', methods=['POST'])
def explain_prediction():
    try:
        model_pipeline = current_app.config['MODEL_PIPELINE']
        core_model = current_app.config['CORE_MODEL']
        data = request.json.get('student_data')
        input_df = pd.DataFrame([data])
        
        preprocessor = model_pipeline.named_steps['preprocessor']
        processed_df = preprocessor.transform(input_df)
        feature_names = preprocessor.get_feature_names_out()
        processed_df = pd.DataFrame(processed_df, columns=feature_names)
        
        explainer = shap.TreeExplainer(core_model)
        shap_values = explainer.shap_values(processed_df)
        
        class_index = list(core_model.classes_).index('High')
        instance_shap = shap_values[class_index][0]
        
        feature_importance = sorted(zip(feature_names, instance_shap), key=lambda x: abs(x[1]), reverse=True)
        
        return jsonify({"explanation": feature_importance[:10]})
    except Exception as e:
        print(f"SHAP explanation error: {e}")
        return jsonify({"error": "Failed to generate explanation."}), 500

@main_bp.route('/generate-advice', methods=['POST'])
def generate_advice_endpoint():
    gemini_api_key = current_app.config['GEMINI_API_KEY']
    data = request.json.get('student_data')
    custom_prompt = data.pop('custom_prompt', '')
    if not data:
        return jsonify({"error": "No student data provided"}), 400

    prompt = f"""
    Role: You are an expert, empathetic, and motivational student mentor.
    Data: {json.dumps(data)}
    
    Task: Generate personalized mentoring advice. Structure your response in Markdown using the following strict format:
    ### 1. Overall Assessment
    ### 2. Key Areas for Focus
    ### 3. Actionable Steps & Strategies
    ### 4. Recommended Resources
    """
    
    if custom_prompt:
        prompt += f"""\n\nAdditional Guidance: The user has a specific request for this advice. Address the following: "{custom_prompt}" """
    
    headers = { 'Content-Type': 'application/json' }
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={gemini_api_key}"
    payload = { "contents": [{"parts": [{"text": prompt}]}] }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        gemini_response = response.json()
        
        text = "Could not generate advice. Please try again."
        if gemini_response and 'candidates' in gemini_response and gemini_response['candidates']:
            text = gemini_response['candidates'][0]['content']['parts'][0]['text']
        
        return jsonify({"advice": text})
    except Exception as e:
        print(f"API call failed: {e}")
        return jsonify({"error": "Failed to connect to the AI service."}), 500

@main_bp.route('/get-grade-averages', methods=['GET'])
def get_grade_averages():
    try:
        df = pd.read_csv('student-por.csv', sep=';')
        grades_avg = df[['G1', 'G2']].mean().to_dict()
        return jsonify(grades_avg)
    except Exception as e:
        print(f"Error fetching grade averages: {e}")
        return jsonify({"error": "Failed to get grades from the dataset."}), 500