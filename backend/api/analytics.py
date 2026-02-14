"""
Analytics API Endpoints for LearnLoop
Provides learning insights and progress analytics
"""
from fastapi import APIRouter, HTTPException
from services.analytics_service import (
    get_learning_velocity,
    get_mastery_heatmap,
    get_study_time_analytics,
    get_ai_insights,
    get_comprehensive_analytics
)

router = APIRouter()

@router.get("/velocity/{user_id}")
async def get_velocity(user_id: int):
    """
    Get learning velocity (concepts per day)
    
    Returns:
    - Average concepts learned per day
    - Trend (increasing/decreasing/stable)
    - Daily breakdown for last 30 days
    """
    try:
        data = await get_learning_velocity(user_id)
        return {
            "status": "success",
            "user_id": user_id,
            "velocity": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate velocity: {str(e)}")

@router.get("/mastery/{user_id}")
async def get_mastery(user_id: int):
    """
    Get mastery heatmap
    
    Returns:
    - Distribution of concepts by mastery level
    - Individual concept mastery scores
    - Total concepts tracked
    """
    try:
        data = await get_mastery_heatmap(user_id)
        return {
            "status": "success",
            "user_id": user_id,
            "mastery": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate mastery: {str(e)}")

@router.get("/study-time/{user_id}")
async def get_study_time(user_id: int):
    """
    Get study time analytics
    
    Returns:
    - Total study time in last 30 days
    - Average session duration
    - Best time of day for studying
    - Session count
    """
    try:
        data = await get_study_time_analytics(user_id)
        return {
            "status": "success",
            "user_id": user_id,
            "study_time": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze study time: {str(e)}")

@router.get("/insights/{user_id}")
async def get_insights(user_id: int):
    """
    Get AI-powered learning insights
    
    Returns:
    - Personalized insights about learning patterns
    - Actionable recommendations
    - AI-generated analysis
    """
    try:
        data = await get_ai_insights(user_id)
        return {
            "status": "success",
            "user_id": user_id,
            "insights": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@router.get("/dashboard/{user_id}")
async def get_analytics_dashboard(user_id: int):
    """
    Get comprehensive analytics dashboard data
    
    Returns all analytics in one call:
    - Learning velocity
    - Mastery heatmap
    - Study time analytics
    - AI insights
    """
    try:
        data = await get_comprehensive_analytics(user_id)
        return {
            "status": "success",
            "dashboard": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard: {str(e)}")
