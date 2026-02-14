"""
AWS Lambda Function: Notification Sender
Sends notifications and reminders to users
"""
import json
import boto3
import os
from datetime import datetime

# Initialize AWS clients
sns_client = boto3.client('sns', region_name=os.getenv('AWS_REGION', 'us-east-1'))

def lambda_handler(event, context):
    """
    Send notifications to users
    
    Event structure:
    {
        "notification_type": "study_reminder|achievement|streak_alert",
        "user_id": 1,
        "user_email": "user@example.com",
        "message": "Time to study!",
        "data": {}
    }
    """
    try:
        notification_type = event.get('notification_type')
        user_id = event.get('user_id')
        user_email = event.get('user_email')
        message = event.get('message')
        data = event.get('data', {})
        
        print(f"Sending {notification_type} notification to user {user_id}")
        
        # Format notification based on type
        if notification_type == "study_reminder":
            subject = "⏰ Time to Study with LAURA!"
            body = format_study_reminder(message, data)
            
        elif notification_type == "achievement":
            subject = "🏆 New Achievement Unlocked!"
            body = format_achievement_notification(message, data)
            
        elif notification_type == "streak_alert":
            subject = "🔥 Keep Your Streak Alive!"
            body = format_streak_alert(message, data)
            
        else:
            subject = "LearnLoop Notification"
            body = message
        
        # Send email via SNS (requires SNS topic setup)
        # For now, just log it
        print(f"Would send email to {user_email}:")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        
        # In production, you would:
        # sns_client.publish(
        #     TopicArn='arn:aws:sns:region:account:learnloop-notifications',
        #     Subject=subject,
        #     Message=body
        # )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Notification sent successfully',
                'user_id': user_id,
                'type': notification_type
            })
        }
        
    except Exception as e:
        print(f"❌ Error sending notification: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to send notification'
            })
        }

def format_study_reminder(message: str, data: dict) -> str:
    """Format study reminder email"""
    return f"""
Hi there! 👋

{message}

Your Stats:
- Current Streak: {data.get('streak_days', 0)} days
- Level: {data.get('level', 1)}
- XP: {data.get('xp', 0)}

Don't break your streak! Study for just 10 minutes today.

Best regards,
LAURA (Your AI Learning Buddy)
"""

def format_achievement_notification(message: str, data: dict) -> str:
    """Format achievement notification email"""
    return f"""
Congratulations! 🎉

{message}

Achievement: {data.get('achievement_name', 'Unknown')}
Reward: +{data.get('xp_reward', 0)} XP

Keep up the amazing work!

Best regards,
LAURA
"""

def format_streak_alert(message: str, data: dict) -> str:
    """Format streak alert email"""
    return f"""
{message}

You're on a {data.get('streak_days', 0)}-day streak! 🔥

Don't let it end! Just 10 minutes of study will keep your streak alive.

Quick Study Options:
- Review a concept with LAURA
- Add notes to your knowledge graph
- Upload new study material

Best regards,
LAURA
"""
