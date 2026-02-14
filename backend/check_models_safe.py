import google.generativeai as genai
import os
from dotenv import load_dotenv
import sys

# Force output to utf-8
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

with open('model_list.txt', 'w', encoding='utf-8') as f:
    if not api_key:
        f.write("❌ API Key not found in .env\n")
    else:
        try:
            genai.configure(api_key=api_key)
            f.write(f"🔑 Testing with API Key found.\n")
            f.write("\n📋 List of Available Models:\n")
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    f.write(f"   - {m.name}\n")
        except Exception as e:
            f.write(f"❌ Error listing models: {e}\n")
