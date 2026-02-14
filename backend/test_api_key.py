"""
Test script to verify Gemini API key is working
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

print("=" * 60)
print("🔍 GEMINI API KEY TEST")
print("=" * 60)

# Get API key
api_key = os.getenv("GEMINI_API_KEY")

print(f"\n1. Checking .env file...")
if api_key:
    print(f"   ✅ API Key found: {api_key[:20]}...{api_key[-4:]}")
else:
    print("   ❌ API Key NOT found in environment")
    print("   📍 Check: backend/.env file")
    exit(1)

print(f"\n2. Configuring Gemini...")
try:
    genai.configure(api_key=api_key)
    print("   ✅ Gemini configured")
except Exception as e:
    print(f"   ❌ Configuration failed: {e}")
    exit(1)

print(f"\n3. Testing API connection...")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Say 'Hello! API is working!' if you can read this.")
    print(f"   ✅ API Response: {response.text}")
    print("\n" + "=" * 60)
    print("🎉 SUCCESS! Your Gemini API key is working perfectly!")
    print("=" * 60)
except Exception as e:
    print(f"   ❌ API Test failed: {e}")
    print("\n" + "=" * 60)
    print("❌ FAILED! API key is invalid or has issues")
    print("=" * 60)
    print("\n💡 Solutions:")
    print("   1. Get a new key: https://aistudio.google.com/app/apikey")
    print("   2. Check if key has expired")
    print("   3. Verify key has no extra spaces")
    exit(1)
