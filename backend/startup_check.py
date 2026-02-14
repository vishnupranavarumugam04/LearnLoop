"""
Startup check - Run this before starting the server
"""
import os
from pathlib import Path

print("=" * 60)
print("🔍 LEARNLOOP STARTUP CHECK")
print("=" * 60)

# Check .env file exists
env_path = Path(__file__).parent / ".env"
print(f"\n1. Checking .env file...")
print(f"   Location: {env_path}")

if env_path.exists():
    print(f"   ✅ File exists")
    
    # Read and display (masked)
    with open(env_path, 'r') as f:
        content = f.read()
    
    if "GEMINI_API_KEY" in content:
        # Extract key
        for line in content.split('\n'):
            if line.startswith('GEMINI_API_KEY='):
                key = line.split('=', 1)[1].strip()
                if key:
                    print(f"   ✅ API Key found: {key[:20]}...{key[-4:]}")
                    print(f"   📏 Key length: {len(key)} characters")
                else:
                    print(f"   ❌ API Key is empty!")
                break
    else:
        print(f"   ❌ GEMINI_API_KEY not found in .env")
else:
    print(f"   ❌ .env file not found!")
    print(f"   💡 Create it at: {env_path}")

# Check if python-dotenv is installed
print(f"\n2. Checking python-dotenv...")
try:
    import dotenv
    print(f"   ✅ python-dotenv installed")
except ImportError:
    print(f"   ❌ python-dotenv NOT installed")
    print(f"   💡 Run: pip install python-dotenv")

# Check if google-generativeai is installed
print(f"\n3. Checking google-generativeai...")
try:
    import google.generativeai
    print(f"   ✅ google-generativeai installed")
except ImportError:
    print(f"   ❌ google-generativeai NOT installed")
    print(f"   💡 Run: pip install google-generativeai")

# Test loading with dotenv
print(f"\n4. Testing environment loading...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print(f"   ✅ API Key loaded: {api_key[:20]}...{api_key[-4:]}")
    else:
        print(f"   ❌ API Key NOT loaded from environment")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ Startup check complete!")
print("=" * 60)
print("\n💡 If all checks pass, restart the server:")
print("   1. Stop: Ctrl+C")
print("   2. Start: python start_project.py")
