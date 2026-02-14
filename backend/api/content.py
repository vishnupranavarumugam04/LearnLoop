"""
Content Provider API Endpoints for LearnLoop
Provides access to external educational content
"""
from fastapi import APIRouter, HTTPException, Query
from services.content_provider_service import (
    search_wikipedia,
    get_youtube_transcript,
    search_educational_content,
    get_related_topics
)

router = APIRouter()

@router.get("/wikipedia/{topic}")
async def get_wikipedia_summary(
    topic: str,
    sentences: int = Query(5, ge=1, le=10, description="Number of sentences in summary")
):
    """
    Get Wikipedia summary for a topic
    
    Args:
        topic: Topic to search
        sentences: Number of sentences to return (1-10)
    
    Returns:
        - Article summary
        - Full URL
        - Page ID
    """
    try:
        data = search_wikipedia(topic, sentences)
        
        if not data.get("found"):
            raise HTTPException(status_code=404, detail=data.get("message", "Article not found"))
        
        return {
            "status": "success",
            "content": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Wikipedia content: {str(e)}")

@router.get("/youtube/{video_id}")
async def get_youtube_transcript_api(video_id: str):
    """
    Get YouTube video transcript
    
    Args:
        video_id: YouTube video ID
    
    Returns:
        - Full transcript
        - Timestamped segments
        - Video URL
    """
    try:
        data = get_youtube_transcript(video_id)
        
        if not data.get("found"):
            raise HTTPException(status_code=404, detail=data.get("message", "Transcript not found"))
        
        return {
            "status": "success",
            "content": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch YouTube transcript: {str(e)}")

@router.get("/search")
async def search_content(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Results per source")
):
    """
    Search educational content from multiple sources
    
    Args:
        query: Search query
        limit: Maximum results per source
    
    Returns:
        Aggregated results from Wikipedia and other sources
    """
    try:
        data = search_educational_content(query, limit)
        
        return {
            "status": "success",
            "results": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/related/{topic}")
async def get_related_topics_api(
    topic: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum related topics")
):
    """
    Get related topics from Wikipedia
    
    Args:
        topic: Main topic
        limit: Maximum number of related topics
    
    Returns:
        List of related topics
    """
    try:
        data = get_related_topics(topic, limit)
        
        return {
            "status": "success",
            "related": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch related topics: {str(e)}")
