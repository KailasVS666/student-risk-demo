from flask import Blueprint, request, jsonify, render_template, current_app
import pandas as pd
import shap
import json
import numpy as np
import google.generativeai as genai
import traceback

# Create a Blueprint, which is a way to organize a group of related views and other code.
main_bp = Blueprint('main', __name__)

def preprocess_student_data(data):
    """
    Takes raw student data, converts it to a DataFrame, and engineers new features.
    This function ensures that the input for prediction and explanation is consistent.
    """
    df = pd.DataFrame([data])
    # Engineer features that might be predictive
    df['grade_change'] = df['G2'] - df['G1']
    df['average_grade'] = (df['G1'] + df['G2']) / 2
    return df

@main_bp.route('/')
def home():
    """Serves the main HTML file for the user interface."""
    return render_template('index.html')

@main_bp.route('/firebase-config')
def firebase_config():
    """Provides the Firebase configuration to the frontend securely."""
    return jsonify(current_app.config['FIREBASE_CONFIG'])

@main_bp.route('/predict-risk', methods=['POST'])
def predict_risk():
    """
    Receives student data, preprocesses it, and returns a risk level prediction.
    """
    try:
        # Load the pre-trained model pipeline and label encoder from the app config
        model_pipeline = current_app.config['MODEL_PIPELINE']
        label_encoder = current_app.config['LABEL_ENCODER']
        
        data = request.json.get('student_data')
        if not data:
            return jsonify({"error": "No student data provided."}), 400

        # Preprocess the incoming data to create the necessary features
        input_df = preprocess_student_data(data)
        
        # Use the pipeline to predict the encoded risk level
        prediction_encoded = model_pipeline.predict(input_df)
        
        # Convert the encoded prediction back to a human-readable label
        risk_label = label_encoder.inverse_transform(prediction_encoded)
        
        return jsonify({'risk_level': risk_label[0]})

    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({"error": "Failed to make a prediction."}), 500

@main_bp.route('/explain-prediction', methods=['POST'])
def explain_prediction():
    """
    Provides a SHAP-based explanation for a prediction, identifying the key factors
    that influenced the model's decision.
    """
    try:
        model_pipeline = current_app.config['MODEL_PIPELINE']
        core_model = current_app.config['CORE_MODEL']
        label_encoder = current_app.config['LABEL_ENCODER']
        
        data = request.json.get('student_data')
        if not data:
            return jsonify({"error": "No student data provided."}), 400
            
        # Preprocess the data just like in the prediction route
        input_df = preprocess_student_data(data)

        # Use the preprocessor from the pipeline to transform the data
        preprocessor = model_pipeline.named_steps['preprocessor']
        processed_data = preprocessor.transform(input_df)
        
        # Create a SHAP explainer and calculate the values
        explainer = shap.TreeExplainer(core_model)
        shap_values = explainer.shap_values(processed_data)
        
        # Find the SHAP values specifically for the 'High' risk class
        high_risk_index = list(label_encoder.classes_).index('High')
        instance_shap = shap_values[high_risk_index][0]
        
        # Get the names of the features after preprocessing
        feature_names = preprocessor.get_feature_names_out()

        # Pair feature names with their SHAP values and sort them by importance
        feature_importance = sorted(zip(feature_names, instance_shap), key=lambda x: abs(x[1]), reverse=True)
        
        # Return the top 10 most influential features
        return jsonify({"explanation": feature_importance[:10]})

    except Exception as e:
        print(f"SHAP explanation error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to generate explanation."}), 500

@main_bp.route('/generate-advice', methods=['POST'])
def generate_advice_endpoint():
    """
    Connects to the Gemini API to generate personalized advice for a student
    based on their data.
    """
    try:
        gemini_api_key = current_app.config['GEMINI_API_KEY']
        data = request.json.get('student_data')
        custom_prompt = data.pop('custom_prompt', '')

        if not data:
            return jsonify({"error": "No student data provided"}), 400

        # Format the student data into a clean, readable string for the prompt
        student_info = "\n".join([f"- {key.replace('_', ' ').title()}: {value}" for key, value in data.items()])

        # Construct the prompt for the generative model
        prompt = f"""
        Role: You are an expert, empathetic, and motivational student mentor.

        Please provide personalized mentoring advice based on the following student information:
        {student_info}

        Task: Structure your response in Markdown using the following strict format:
        ### 1. Overall Assessment
        ### 2. Key Areas for Focus
        ### 3. Actionable Steps & Strategies
        ### 4. Recommended Resources
        """
        
        if custom_prompt:
            prompt += f"\n\nAdditional Guidance: Please also address the user's specific request: {custom_prompt}"
        
        genai.configure(api_key=gemini_api_key)
        
        # --- THIS IS THE NEW, CORRECT MODEL NAME FROM YOUR LIST ---
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        response = model.generate_content(prompt)
        
        return jsonify({"advice": response.text})

    except Exception as e:
        print("--- DETAILED GEMINI API ERROR ---")
        traceback.print_exc()
        return jsonify({"error": "Failed to connect to the AI service."}), 500

@main_bp.route('/get-grade-averages', methods=['GET'])
def get_grade_averages():
    """
    Efficiently retrieves the pre-calculated grade averages from the app's configuration.
    """
    try:
        # This is much more efficient than reading the CSV on every request
        grades_avg = current_app.config.get('GRADE_AVERAGES')
        if grades_avg is None:
            return jsonify({"error": "Grade averages not found in app configuration."}), 500
        return jsonify(grades_avg)
    except Exception as e:
        print(f"Error fetching grade averages: {e}")
        return jsonify({"error": "Failed to retrieve grade averages."}), 500