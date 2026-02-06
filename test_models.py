import google.generativeai as genai
import os

# Paste your key here for the test
GOOGLE_API_KEY = "AIzaSyCO4d6U-okdVTqkHj3UK60IYARfDzOiMeI"
genai.configure(api_key=GOOGLE_API_KEY)

print("Checking available models for your API key...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")