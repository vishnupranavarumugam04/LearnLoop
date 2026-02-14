from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict

router = APIRouter()

# --- Models ---
class UserProfile(BaseModel):
    user_name: str
    level: int = 1
    total_xp: int = 0
    streak_days: int = 1
    global_rank_percent: int = 100
    role: str = "Scholar"
    bio: str = "Ready to learn!"
    university: str = "LearnLoop University"
    buddy_name: str = "Buddy"
    buddy_avatar: str = "seedling"
    last_study_date: Optional[str] = None
    subjects: Dict[str, int] = {}
    badges: List[str] = ["First Lesson"]
    settings: Dict[str, bool] = {
        "dark_mode": True,
        "high_contrast": False,
        "notifications_study": True,
        "notifications_battle": True
    }

# --- Endpoints ---

@router.get("/{user_name}", response_model=UserProfile)
async def get_profile(user_name: str):
    """Get user profile from database"""
    from database import get_user_by_username, get_user_profile, create_user
    
    # Get or create user
    user = get_user_by_username(user_name)
    if not user:
        # Create new user
        user_id = create_user(user_name, "default_hash", user_name)
        if not user_id:
            raise HTTPException(status_code=500, detail="Failed to create user")
    else:
        user_id = user['id']
    
    # Get full profile
    profile = get_user_profile(user_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    from database import get_user_percentile
    rank_percent = get_user_percentile(user_id)
    
    return UserProfile(
        user_name=profile.get('full_name') or profile['username'],
        level=profile.get('level', 1),
        total_xp=profile.get('total_xp', 0),
        streak_days=profile.get('streak_days', 0),
        global_rank_percent=rank_percent,
        bio=profile.get('bio', "Ready to learn!"),
        university=profile.get('university', "LearnLoop University"),
        buddy_name=profile.get('buddy_name', "Buddy"),
        buddy_avatar=profile.get('buddy_avatar', "seedling"),
        last_study_date=profile.get('last_study_date'),
        settings=profile.get('settings', {})
    )

class UpdateProfileRequest(BaseModel):
    bio: Optional[str] = None
    university: Optional[str] = None
    subjects: Optional[Dict[str, int]] = None
    buddy_name: Optional[str] = None
    buddy_avatar: Optional[str] = None
    settings: Optional[Dict[str, bool]] = None

@router.patch("/{user_name}")
async def update_profile(user_name: str, req: UpdateProfileRequest):
    """Update user profile"""
    from database import get_user_by_username
    
    user = get_user_by_username(user_name)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    from database import update_user_settings
    
    if req.settings is not None:
        update_user_settings(user['id'], req.settings)
    
    if req.bio is not None or req.university is not None:
        from database import update_user_profile
        update_user_profile(user['id'], req.bio, req.university)
    
    if req.buddy_name is not None or req.buddy_avatar is not None:
        from database import update_buddy_profile, get_user_profile
        p = get_user_profile(user['id'])
        name = req.buddy_name if req.buddy_name is not None else p.get('buddy_name', 'Buddy')
        avatar = req.buddy_avatar if req.buddy_avatar is not None else p.get('buddy_avatar', 'seedling')
        update_buddy_profile(user['id'], name, avatar)
    
    return await get_profile(user_name)

