from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import google.generativeai as genai
from datetime import datetime

router = APIRouter()

class APIKeyTest(BaseModel):
    api_key: str

class HealthResponse(BaseModel):
    status: str
    gemini_configured: bool
    gemini_working: bool
    database_connected: bool
    timestamp: str
    message: str

@router.get("/", response_model=HealthResponse)
async def health_check():
    """Check overall API health"""
    
    # Check if Gemini API key is configured
    api_key = os.getenv("GEMINI_API_KEY")
    gemini_configured = bool(api_key and api_key != "")
    
    # Test Gemini API
    gemini_working = False
    if gemini_configured:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content("Say 'OK' if you're working")
            gemini_working = "ok" in response.text.lower()
        except Exception as e:
            print(f"Gemini test failed: {e}")
            gemini_working = False
    
    # Check database
    database_connected = False
    try:
        from database import get_db
        conn = get_db()
        conn.close()
        database_connected = True
    except Exception as e:
        print(f"Database test failed: {e}")
    
    # Overall status
    all_good = gemini_configured and gemini_working and database_connected
    
    return {
        "status": "healthy" if all_good else "degraded",
        "gemini_configured": gemini_configured,
        "gemini_working": gemini_working,
        "database_connected": database_connected,
        "timestamp": datetime.now().isoformat(),
        "message": "All systems operational" if all_good else "Some services unavailable"
    }

@router.post("/test-key")
async def test_api_key(data: APIKeyTest):
    """Test a Gemini API key"""
    try:
        genai.configure(api_key=data.api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Respond with exactly: 'API key is valid'")
        
        if "valid" in response.text.lower():
            return {
                "status": "success",
                "message": "API key is valid and working!",
                "response": response.text
            }
        else:
            return {
                "status": "warning",
                "message": "API key works but got unexpected response",
                "response": response.text
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"API key test failed: {str(e)}"
        }

@router.get("/gemini-status")
async def gemini_status():
    """Quick Gemini API status check"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return {
            "configured": False,
            "working": False,
            "message": "No API key configured. Add GEMINI_API_KEY to backend/.env"
        }
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Hi")
        
        return {
            "configured": True,
            "working": True,
            "message": "Gemini API is working perfectly!",
            "model": "gemini-flash-latest"
        }
    except Exception as e:
        return {
            "configured": True,
            "working": False,
            "message": f"API key configured but not working: {str(e)}"
        }
