"""
Analytics Service for LearnLoop
Provides learning insights and progress analytics
"""
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np

class AnalyticsService:
    """
    Analytics service for learning insights
    Tracks learning velocity, retention, and provides predictions
    """
    
    def __init__(self):
        pass
    
    async def calculate_learning_velocity(self, user_id: int) -> Dict:
        """
        Calculate concepts learned per day (learning velocity)
        
        Args:
            user_id: ID of user
        
        Returns:
            Learning velocity metrics
        """
        from database import get_db
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get concepts learned in last 30 days
        cursor.execute("""
            SELECT DATE(first_learned) as learn_date, COUNT(*) as count
            FROM knowledge_nodes 
            WHERE user_id = ? 
            AND first_learned >= DATE('now', '-30 days')
            GROUP BY DATE(first_learned)
            ORDER BY learn_date
        """, (user_id,))
        
        daily_data = cursor.fetchall()
        conn.close()
        
        if not daily_data:
            return {
                "average_concepts_per_day": 0,
                "trend": "no_data",
                "total_concepts_30_days": 0,
                "daily_breakdown": []
            }
        
        # Calculate average
        total_concepts = sum(row[1] for row in daily_data)
        days_with_activity = len(daily_data)
        avg_velocity = total_concepts / max(days_with_activity, 1)
        
        # Calculate trend (simple linear regression)
        if len(daily_data) > 1:
            x = np.arange(len(daily_data))
            y = np.array([row[1] for row in daily_data])
            slope = np.polyfit(x, y, 1)[0]
            trend = "increasing" if slope > 0.1 else ("decreasing" if slope < -0.1 else "stable")
        else:
            trend = "stable"
        
        return {
            "average_concepts_per_day": round(avg_velocity, 2),
            "trend": trend,
            "total_concepts_30_days": total_concepts,
            "days_active_30_days": days_with_activity,
            "daily_breakdown": [
                {"date": row[0], "concepts": row[1]} 
                for row in daily_data
            ]
        }
    
    async def calculate_mastery_heatmap(self, user_id: int) -> Dict:
        """
        Calculate concept mastery levels
        
        Args:
            user_id: ID of user
        
        Returns:
            Mastery heatmap data
        """
        from database import get_knowledge_graph
        
        knowledge = get_knowledge_graph(user_id)
        nodes = knowledge.get('nodes', [])
        
        # Group by mastery level
        mastery_distribution = {
            "beginner": 0,
            "intermediate": 0,
            "advanced": 0,
            "expert": 0
        }
        
        concept_details = []
        
        for node in nodes:
            mastery = node.get('mastery_level', 0)
            name = node.get('name', 'Unknown')
            
            # Categorize mastery
            if mastery < 0.25:
                category = "beginner"
            elif mastery < 0.5:
                category = "intermediate"
            elif mastery < 0.75:
                category = "advanced"
            else:
                category = "expert"
            
            mastery_distribution[category] += 1
            
            concept_details.append({
                "name": name,
                "mastery_level": mastery,
                "category": category,
                "reviews": node.get('review_count', 0)
            })
        
        return {
            "distribution": mastery_distribution,
            "total_concepts": len(nodes),
            "concepts": sorted(concept_details, key=lambda x: x['mastery_level'], reverse=True)
        }
    
    async def calculate_study_time_analytics(self, user_id: int) -> Dict:
        """
        Calculate study time patterns
        
        Args:
            user_id: IDof user
        
        Returns:
            Study time analytics
        """
        from database import get_db
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get study sessions from last 30 days
        cursor.execute("""
            SELECT 
                created_at,
                duration_minutes
            FROM study_sessions
            WHERE user_id = ?
            AND created_at >= DATE('now', '-30 days')
            ORDER BY created_at
        """, (user_id,))
        
        sessions = cursor.fetchall()
        conn.close()
        
        if not sessions:
            return {
                "total_study_time_minutes": 0,
                "average_session_minutes": 0,
                "sessions_count": 0,
                "best_time_of_day": "No data"
            }
        
        total_time = sum(s[1] for s in sessions if s[1])
        session_count = len(sessions)
        avg_time = total_time / max(session_count, 1)
        
        # Analyze time of day (simple analysis)
        hour_counts = {}
        for session in sessions:
            try:
                dt = datetime.fromisoformat(session[0])
                hour = dt.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            except:
                pass
        
        best_hour = max(hour_counts, key=hour_counts.get) if hour_counts else 12
        
        # Convert hour to time period
        if 5 <= best_hour < 12:
            best_time = "Morning (5 AM - 12 PM)"
        elif 12 <= best_hour < 17:
            best_time = "Afternoon (12 PM - 5 PM)"
        elif 17 <= best_hour < 21:
            best_time = "Evening (5 PM - 9 PM)"
        else:
            best_time = "Night (9 PM - 5 AM)"
        
        return {
            "total_study_time_minutes": total_time,
            "total_study_time_hours": round(total_time / 60, 1),
            "average_session_minutes": round(avg_time, 1),
            "sessions_count": session_count,
            "best_time_of_day": best_time
        }
    
    async def generate_ai_insights(self, user_id: int) -> Dict:
        """
        Generate AI-powered learning insights using Gemini
        
        Args:
            user_id: ID of user
        
        Returns:
            AI-generated insights
        """
        import google.generativeai as genai
        import os
        
        # Get analytics data
        velocity = await self.calculate_learning_velocity(user_id)
        mastery = await self.calculate_mastery_heatmap(user_id)
        study_time = await self.calculate_study_time_analytics(user_id)
        
        # Prepare data summary for AI
        data_summary = f"""
        Learning Velocity: {velocity['average_concepts_per_day']} concepts/day, Trend: {velocity['trend']}
        Mastery Distribution: {mastery['distribution']}
        Study Time: {study_time['total_study_time_hours']} hours in last 30 days
        Best Study Time: {study_time['best_time_of_day']}
        """
        
        # Generate insights using Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {
                "insights": [
                    "Continue your consistent study habits!",
                    f"You're learning at {velocity['average_concepts_per_day']} concepts/day",
                    "Keep up the great work!"
                ],
                "recommendations": [
                    "Review concepts with low mastery levels",
                    "Maintain your current study schedule"
                ],
                "ai_powered": False
            }
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            prompt = f"""
            Analyze this student's learning data and provide 3-5 specific insights and 2-3 actionable recommendations:
            
            {data_summary}
            
            Format as JSON with keys: "insights" (array of strings) and "recommendations" (array of strings).
            Keep insights encouraging but realistic. Focus on patterns and improvement areas.
            """
            
            response = model.generate_content(prompt)
            
            # Try to parse JSON from response
            import json
            import re
            
            text = response.text
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            
            insights_data = json.loads(text)
            insights_data['ai_powered'] = True
            
            return insights_data
            
        except Exception as e:
            print(f"AI insight generation error: {e}")
            return {
                "insights": [
                    "Your learning pattern shows consistency",
                    f"Focus on mastering {mastery['distribution']['beginner']} beginner concepts",
                    f"You study best during {study_time['best_time_of_day']}"
                ],
                "recommendations": [
                    "Review concepts with less than 50% mastery",
                    "Stick to your productive study times"
                ],
                "ai_powered": False
            }
    
    async def get_comprehensive_analytics(self, user_id: int) -> Dict:
        """
        Get all analytics in one call
        
        Args:
            user_id: ID of user
        
        Returns:
            Complete analytics dashboard data
        """
        velocity = await self.calculate_learning_velocity(user_id)
        mastery = await self.calculate_mastery_heatmap(user_id)
        study_time = await self.calculate_study_time_analytics(user_id)
        insights = await self.generate_ai_insights(user_id)
        
        return {
            "user_id": user_id,
            "generated_at": datetime.now().isoformat(),
            "learning_velocity": velocity,
            "mastery_heatmap": mastery,
            "study_time": study_time,
            "ai_insights": insights
        }

# Global analytics service instance
analytics_service = AnalyticsService()

# Convenience functions
async def get_learning_velocity(user_id: int) -> Dict:
    """Get learning velocity for user"""
    return await analytics_service.calculate_learning_velocity(user_id)

async def get_mastery_heatmap(user_id: int) -> Dict:
    """Get mastery heatmap for user"""
    return await analytics_service.calculate_mastery_heatmap(user_id)

async def get_study_time_analytics(user_id: int) -> Dict:
    """Get study time analytics for user"""
    return await analytics_service.calculate_study_time_analytics(user_id)

async def get_ai_insights(user_id: int) -> Dict:
    """Get AI-powered insights for user"""
    return await analytics_service.generate_ai_insights(user_id)

async def get_comprehensive_analytics(user_id: int) -> Dict:
    """Get all analytics for user"""
    return await analytics_service.get_comprehensive_analytics(user_id)
