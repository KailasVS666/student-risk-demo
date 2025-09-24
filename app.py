from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
import json
import joblib
import pandas as pd
import shap # Import the SHAP library

# Load environment variables from the .env file
load_dotenv()
app = Flask(__name__)
CORS(app)

# --- ML Model Loading ---
# Load the full pipeline which includes the preprocessor
model_pipeline = joblib.load('early_warning_model_pipeline.joblib')
# Load the core classifier model for SHAP explanations
core_model = joblib.load('student_risk_classifier.joblib')

# Load the Gemini API Key from the environment variables
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file.")

@app.route('/')
def home():
    """Serves the main HTML file from the templates folder."""
    return render_template('index.html')

@app.route('/firebase-config')
def firebase_config():
    config = {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID"),
    }
    return jsonify(config)

@app.route('/predict-risk', methods=['POST'])
def predict_risk():
    try:
        data = request.json.get('student_data')
        input_df = pd.DataFrame([data])
        prediction = model_pipeline.predict(input_df)
        risk_label = prediction[0]
        return jsonify({'risk_level': risk_label})
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({"error": "Failed to make a prediction."}), 500

# --- NEW ENDPOINT FOR SHAP EXPLANATIONS ---
@app.route('/explain-prediction', methods=['POST'])
def explain_prediction():
    try:
        data = request.json.get('student_data')
        input_df = pd.DataFrame([data])

        # Get the preprocessor from the pipeline
        preprocessor = model_pipeline.named_steps['preprocessor']
        
        # Transform the input data using the preprocessor
        processed_df = preprocessor.transform(input_df)
        
        # We need the feature names after one-hot encoding
        feature_names = preprocessor.get_feature_names_out()
        processed_df = pd.DataFrame(processed_df, columns=feature_names)

        # Create a SHAP explainer and get shap values
        explainer = shap.TreeExplainer(core_model)
        shap_values = explainer.shap_values(processed_df)

        # We'll focus on the explanation for the "High" risk class (index 1)
        # Note: The index might change if your model's classes_ attribute is different
        # Check `core_model.classes_` to be sure. Assumes ['High', 'Low', 'Medium'] or similar.
        class_index = list(core_model.classes_).index('High') # Find index for 'High' risk
        
        # Get the SHAP values for the specific prediction
        instance_shap = shap_values[class_index][0]

        # Create a list of feature names and their SHAP values
        feature_importance = sorted(
            zip(feature_names, instance_shap),
            key=lambda x: abs(x[1]),
            reverse=True
        )

        # Return the top 10 most influential features
        return jsonify({"explanation": feature_importance[:10]})

    except Exception as e:
        print(f"SHAP explanation error: {e}")
        return jsonify({"error": "Failed to generate explanation."}), 500
# ---------------------------------------------

@app.route('/generate-advice', methods=['POST'])
def generate_advice_endpoint():
    data = request.json.get('student_data')
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

    headers = { 'Content-Type': 'application/json' }
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    payload = { "contents": [{"parts": [{"text": prompt}]}] }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        gemini_response = response.json()
        
        text = "Could not generate advice. Please try again."
        if gemini_response and 'candidates' in gemini_response and gemini_response['candidates']:
            text = gemini_response['candidates'][0]['content']['parts'][0]['text']

        return jsonify({"advice": text})

    except requests.exceptions.RequestException as e:
        print(f"API call failed: {e}")
        if e.response:
            print(f"Google API Error: {e.response.text}")
        return jsonify({"error": f"Failed to connect to the AI service: {e}"}), 500
    except (KeyError, IndexError) as e:
        print(f"Invalid API response format: {e}")
        return jsonify({"error": "Invalid response from the AI service."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8501)