from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
import json

# Load environment variables from the .env file
load_dotenv()
app = Flask(__name__)
CORS(app)

# Load the Gemini API Key from the environment variables
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file.")

@app.route('/')
def home():
    """Serves the main HTML file from the templates folder."""
    return render_template('index.html')

# NEW: Add an endpoint to serve the Firebase config securely
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

@app.route('/generate-advice', methods=['POST'])
def generate_advice_endpoint():
    """
    Acts as a secure proxy to the Gemini API.
    It receives student data and calls the Gemini API to generate advice.
    """
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

    headers = {
        'Content-Type': 'application/json'
    }
    # === THIS LINE HAS BEEN UPDATED ===
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        gemini_response = response.json()
        
        # Extract the generated text
        if gemini_response and 'candidates' in gemini_response:
            text = gemini_response['candidates'][0]['content']['parts'][0]['text']
        else:
            text = "Could not generate advice. Please try again."

        return jsonify({"advice": text})

    except requests.exceptions.RequestException as e:
        print(f"API call failed: {e}")
        # Add this line to see the detailed error from Google
        if e.response:
            print(f"Google API Error: {e.response.text}")
        return jsonify({"error": f"Failed to connect to the AI service: {e}"}), 500
    except (KeyError, IndexError) as e:
        print(f"Invalid API response format: {e}")
        return jsonify({"error": "Invalid response from the AI service."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8501)