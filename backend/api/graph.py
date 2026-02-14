from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict

router = APIRouter()

class GraphRequest(BaseModel):
    user_id: Optional[int] = 1

@router.get("/")
async def get_knowledge_graph(user_id: Optional[int] = 1, username: Optional[str] = None):
    """Get dynamic knowledge graph showing ONLY study materials orbiting YOU"""
    from database import get_db, get_user_by_username
    
    active_user_id = user_id
    if username:
        user = get_user_by_username(username)
        if user:
            active_user_id = user['id']
            
    # Fetch Materials from DB
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, uploaded_at, learning_stage, xp_earned_total FROM study_materials WHERE user_id = ? ORDER BY uploaded_at DESC", (active_user_id,))
    materials = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Build Graph Structure
    nodes_response = []
    links_response = []
    
    # Standard labels
    user_label = "YOU"
    
    # 1. Process Materials as Nodes
    for mat in materials:
        # Determine status and color based on learning_stage
        stage = mat.get('learning_stage', 'uploaded')
        color = "#ef4444" # red for uploaded
        if stage == 'mastered':
            color = "#3b82f6" # blue
        elif stage == 'user_taught':
            color = "#22c55e" # green
        elif stage == 'buddy_taught':
            color = "#eab308" # yellow
            
        # Size grows with XP: base 30 + (xp / 5)
        xp = mat.get('xp_earned_total', 0)
        size = 30 + (xp / 5)
        
        nodes_response.append({
            "id": mat['filename'],
            "label": mat['filename'],
            "subject": "Material",
            "mastery": xp,
            "status": stage,
            "color": color,
            "val": size,
            "difficulty": "N/A",
            "description": f"Study progress: {stage}"
        })
        
        # Connect to central YOU
        links_response.append({
            "source": user_label,
            "target": mat['filename'],
            "type": "learning",
            "strength": 0.8
        })

    return {
        "nodes": nodes_response,
        "links": links_response,
        "total_concepts": len(materials),
        "mastery_summary": {
            "mastered": len([n for n in nodes_response if n["status"] == "mastered"]),
            "learning": len([n for n in nodes_response if n["status"] != "mastered"]),
            "total": len(nodes_response)
        },
        "graph_health": {
            "density": 0.5,
            "is_connected": True,
            "number_of_islands": 0
        }
    }
