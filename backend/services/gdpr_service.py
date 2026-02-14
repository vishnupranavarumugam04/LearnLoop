"""
GDPR Service for LearnLoop
Implements data protection and user rights
"""
import json
from datetime import datetime
from typing import Dict, List
import os

class GDPRService:
    """
    GDPR compliance service
    Handles data export, deletion, consent management
    """
    
    def __init__(self):
        self.consent_data = {}
    
    async def export_user_data(self, user_id: int) -> Dict:
        """
        Export all user data (GDPR Right to Access)
        
        Args:
            user_id: ID of user requesting data export
        
        Returns:
            Complete user data in portable format
        """
        from database import (
            get_user_profile, get_chat_sessions, get_chat_history,
            get_knowledge_graph, get_db
        )
        
        # Get user profile
        profile = get_user_profile(user_id)
        if not profile:
            return {"error": "User not found"}
        
        # Get study materials
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM study_materials WHERE user_id = ?", (user_id,))
        materials = [dict(row) for row in cursor.fetchall()]
        
        # Get study sessions
        cursor.execute("SELECT * FROM study_sessions WHERE user_id = ?", (user_id,))
        sessions = [dict(row) for row in cursor.fetchall()]
        
        # Get achievements
        cursor.execute("SELECT * FROM achievements WHERE user_id = ?", (user_id,))
        achievements = [dict(row) for row in cursor.fetchall()]
        
        # Get study rooms participated in
        cursor.execute("""
            SELECT sr.*, rp.joined_at 
            FROM study_rooms sr
            JOIN room_participants rp ON sr.id = rp.room_id
            WHERE rp.user_id = ?
        """, (user_id,))
        rooms = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # Get chat sessions and history
        chat_sessions = get_chat_sessions(user_id)
        all_chat_history = []
        for session in chat_sessions:
            history = get_chat_history(user_id, session_id=session['id'])
            all_chat_history.append({
                'session': session,
                'messages': history
            })
        
        # Get knowledge graph
        knowledge = get_knowledge_graph(user_id)
        
        # Compile all data
        export_data = {
            "export_info": {
                "user_id": user_id,
                "exported_at": datetime.now().isoformat(),
                "format_version": "1.0"
            },
            "personal_data": {
                "username": profile.get('username'),
                "full_name": profile.get('full_name'),
                "email": profile.get('username'),  # Using username as email
                "created_at": profile.get('created_at'),
                "bio": profile.get('bio'),
                "university": profile.get('university')
            },
            "learning_data": {
                "profile": {
                    "level": profile.get('level'),
                    "total_xp": profile.get('total_xp'),
                    "streak_days": profile.get('streak_days'),
                    "last_study_date": profile.get('last_study_date')
                },
                "buddy": {
                    "name": profile.get('buddy_name'),
                    "avatar": profile.get('buddy_avatar')
                },
                "materials": materials,
                "sessions": sessions,
                "achievements": achievements,
                "knowledge_graph": knowledge
            },
            "communication_data": {
                "chat_history": all_chat_history,
                "study_rooms": rooms
            },
            "metadata": {
                "total_materials": len(materials),
                "total_sessions": len(sessions),
                "total_achievements": len(achievements),
                "total_chat_messages": sum(len(ch['messages']) for ch in all_chat_history),
                "total_concepts_learned": len(knowledge.get('nodes', []))
            }
        }
        
        return export_data
    
    async def delete_all_user_data(self, user_id: int, confirmation: str) -> bool:
        """
        Permanently delete all user data (GDPR Right to be Forgotten)
        
        Args:
            user_id: ID of user to delete
            confirmation: Must be "DELETE_MY_ACCOUNT_PERMANENTLY"
        
        Returns:
            True if deletion successful, False otherwise
        """
        if confirmation != "DELETE_MY_ACCOUNT_PERMANENTLY":
            raise ValueError("Invalid confirmation string")
        
        from database import delete_user
        
        # Delete from database (cascades to all related tables)
        success = delete_user(user_id)
        
        if success:
            # Delete uploaded files
            await self._delete_user_files(user_id)
            
            # Delete S3 files if AWS is enabled
            try:
                from services.s3_service import s3_service
                if s3_service.use_s3:
                    await self._delete_s3_files(user_id)
            except:
                pass
            
            # Log deletion (for compliance audit trail)
            print(f"🗑️  User {user_id} data permanently deleted at {datetime.now().isoformat()}")
            
        return success
    
    async def _delete_user_files(self, user_id: int):
        """Delete local uploaded files for user"""
        import shutil
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
        user_dir = os.path.join(uploads_dir, f"user_{user_id}")
        
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
            print(f"✅ Deleted local files for user {user_id}")
    
    async def _delete_s3_files(self, user_id: int):
        """Delete S3 files for user"""
        from services.s3_service import s3_service
        
        try:
            # List and delete all files in user's S3 prefix
            if s3_service.s3_client:
                prefix = f"materials/user_{user_id}/"
                response = s3_service.s3_client.list_objects_v2(
                    Bucket=s3_service.bucket_name,
                    Prefix=prefix
                )
                
                if 'Contents' in response:
                    for obj in response['Contents']:
                        s3_service.s3_client.delete_object(
                            Bucket=s3_service.bucket_name,
                            Key=obj['Key']
                        )
                    print(f"✅ Deleted {len(response['Contents'])} S3 files for user {user_id}")
        except Exception as e:
            print(f"⚠️  S3 deletion error: {e}")
    
    def get_data_usage_info(self, user_id: int) -> Dict:
        """
        Get information about what data is collected and how it's used
        
        Args:
            user_id: ID of user
        
        Returns:
            Data usage information
        """
        return {
            "data_collected": {
                "personal_information": [
                    "Username",
                    "Full name",
                    "Password (hashed)",
                    "Bio",
                    "University name"
                ],
                "learning_data": [
                    "Study materials (files you upload)",
                    "Chat conversations with AI Buddy",
                    "Knowledge graph (concepts learned)",
                    "XP and level progression",
                    "Study sessions and duration",
                    "Achievements unlocked"
                ],
                "activity_data": [
                    "Study room participation",
                    "Last login date",
                    "Streak tracking",
                    "Material interaction logs"
                ]
            },
            "data_usage": {
                "purpose": "To provide personalized AI-powered learning experiences",
                "storage": {
                    "database": "SQLite (local) or DynamoDB (cloud)",
                    "files": "Local filesystem or AWS S3",
                    "logs": "Console or AWS CloudWatch"
                },
                "retention": "Data is retained until you delete your account",
                "sharing": "Data is NEVER shared with third parties"
            },
            "your_rights": {
                "access": "Export all your data at any time",
                "rectification": "Update your profile information",
                "erasure": "Delete your account and all data permanently",
                "portability": "Download your data in JSON format"
            },
            "security": {
                "encryption": "Chat messages and files are encrypted",
                "authentication": "Passwords are hashed with bcrypt",
                "access_control": "Only you can access your data"
            },
            "contact": {
                "privacy_questions": "Contact your system administrator",
                "data_requests": "Use the Privacy Dashboard"
            }
        }

# Global GDPR service instance
gdpr_service = GDPRService()

# Convenience functions
async def export_user_data(user_id: int) -> Dict:
    """Export all user data"""
    return await gdpr_service.export_user_data(user_id)

async def delete_all_user_data(user_id: int, confirmation: str) -> bool:
    """Permanently delete all user data"""
    return await gdpr_service.delete_all_user_data(user_id, confirmation)

def get_data_usage_info(user_id: int) -> Dict:
    """Get data usage information"""
    return gdpr_service.get_data_usage_info(user_id)
