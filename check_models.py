import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load your API key from the .env file
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ GOOGLE_API_KEY not found in .env file.")
else:
    try:
        genai.configure(api_key=api_key)
        
        print("🔍 Finding available Gemini models...\n")
        
        # This is the 'ListModels' call the error suggested
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"✅ Model Name: {model.name}")
                
    except Exception as e:
        print(f"An error occurred: {e}")
