"""
GDPR API Endpoints for LearnLoop
Implements GDPR compliance endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from services.gdpr_service import export_user_data, delete_all_user_data, get_data_usage_info
import json

router = APIRouter()

class ExportRequest(BaseModel):
    user_id: int

class DeleteRequest(BaseModel):
    user_id: int
    confirmation: str

@router.get("/export-data/{user_id}")
async def export_my_data(user_id: int):
    """
    Export all user data in JSON format (GDPR Right to Access)
    
    Returns complete data export including:
    - Personal information
    - Learning data (materials, sessions, XP)
    - Chat history
    - Knowledge graph
    - Study room participation
    """
    try:
        data = await export_user_data(user_id)
        
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        
        return {
            "status": "success",
            "message": "Data export complete",
            "data": data,
            "download_info": {
                "format": "JSON",
                "size_estimate": f"{len(json.dumps(data)) / 1024:.2f} KB"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/delete-account")
async def delete_my_account(request: DeleteRequest):
    """
    Permanently delete account and all data (GDPR Right to be Forgotten)
    
    WARNING: This action is IRREVERSIBLE!
    - All personal data will be deleted
    - All learning progress will be lost
    - All uploaded materials will be removed
    - All chat history will be erased
    
    Requires confirmation string: "DELETE_MY_ACCOUNT_PERMANENTLY"
    """
    try:
        success = await delete_all_user_data(request.user_id, request.confirmation)
        
        if success:
            return {
                "status": "deleted",
                "message": "Account and all data permanently deleted",
                "deleted_at": "2026-02-06T14:30:00Z",  # Use actual timestamp
                "recoverable": False
            }
        else:
            raise HTTPException(status_code=500, detail="Deletion failed")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

@router.get("/data-usage/{user_id}")
async def show_data_usage(user_id: int):
    """
    Show what data is collected and how it's used (GDPR Transparency)
    
    Returns:
    - What data is collected
    - Why it's collected
    - How it's stored
    - Your rights
    - Security measures
    """
    try:
        info = get_data_usage_info(user_id)
        return {
            "status": "success",
            "user_id": user_id,
            "privacy_info": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve data usage info: {str(e)}")

@router.get("/privacy-policy")
async def get_privacy_policy():
    """
    Get privacy policy
    """
    return {
        "version": "1.0",
        "last_updated": "2026-02-06",
        "policy": {
            "introduction": "LearnLoop is committed to protecting your privacy and personal data.",
            "data_controller": "LearnLoop Team",
            "legal_basis": "Consent and legitimate interest in providing educational services",
            "data_retention": "Data is retained until you delete your account",
            "third_parties": "We do not share your data with third parties",
            "cookies": "We use essential cookies for authentication only",
            "your_rights": [
                "Right to access your data",
                "Right to rectify incorrect data",
                "Right to erase your data",
                "Right to data portability",
                "Right to object to processing",
                "Right to withdraw consent"
            ],
            "contact": "privacy@learnloop.ai",
            "gdpr_compliance": "Fully compliant with GDPR regulations"
        }
    }

@router.get("/download-data/{user_id}")
async def download_data_file(user_id: int):
    """
    Download user data as downloadable JSON file
    """
    from fastapi.responses import JSONResponse
    
    try:
        data = await export_user_data(user_id)
        
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        
        # Return as downloadable file
        return JSONResponse(
            content=data,
            headers={
                "Content-Disposition": f'attachment; filename="learnloop_data_user_{user_id}.json"',
                "Content-Type": "application/json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
