import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("Listing all available models to models.json...")
try:
    models = []
    for m in genai.list_models():
        models.append({
            "name": m.name,
            "display_name": m.display_name,
            "supported_methods": m.supported_generation_methods
        })
    with open("models.json", "w") as f:
        json.dump(models, f, indent=2)
    print(f"Success! Found {len(models)} models.")
except Exception as e:
    print(f"Error: {e}")

