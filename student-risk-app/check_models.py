import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load the environment variables from your .env file
load_dotenv()

# Configure the API with your key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env file.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

    print("--- Models Available to Your API Key ---")
    for m in genai.list_models():
        # Check if the model supports the 'generateContent' method
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
    print("----------------------------------------")