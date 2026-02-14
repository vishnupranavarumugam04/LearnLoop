"""
Lambda Service for LearnLoop
Handles invocation of AWS Lambda functions
"""
import boto3
import json
import os
from typing import Dict

class LambdaService:
    """
    Service for invoking AWS Lambda functions
    """
    
    def __init__(self):
        """Initialize Lambda client"""
        self.lambda_client = None
        self.use_lambda = os.getenv("USE_LAMBDA", "false").lower() == "true"
        
        if self.use_lambda:
            try:
                self.lambda_client = boto3.client(
                    'lambda',
                    region_name=os.getenv("AWS_REGION", "us-east-1")
                )
                print("✅ Lambda service initialized")
            except Exception as e:
                print(f"⚠️  Lambda initialization failed: {e}")
                self.use_lambda = False
    
    def invoke_material_processor(self, s3_key: str, user_id: int, material_id: int) -> Dict:
        """
        Invoke material processor Lambda asynchronously
        
        Args:
            s3_key: S3 key of uploaded material
            user_id: User ID
            material_id: Material ID
        
        Returns:
            Invocation result
        """
        if not self.use_lambda or not self.lambda_client:
            print("⚠️  Lambda not enabled, processing would happen synchronously")
            return {
                "success": False,
                "message": "Lambda not configured"
            }
        
        try:
            payload = {
                "s3_key": s3_key,
                "user_id": user_id,
                "material_id": material_id,
                "bucket_name": os.getenv("S3_BUCKET_NAME", "learnloop-materials")
            }
            
            response = self.lambda_client.invoke(
                FunctionName='learnloop-material-processor',
                InvocationType='Event',  # Async invocation
                Payload=json.dumps(payload)
            )
            
            print(f"✅ Lambda invoked for material processing: {material_id}")
            
            return {
                "success": True,
                "request_id": response.get('ResponseMetadata', {}).get('RequestId'),
                "status_code": response['StatusCode']
            }
            
        except Exception as e:
            print(f"❌ Lambda invocation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def invoke_notification_sender(
        self,
        notification_type: str,
        user_id: int,
        user_email: str,
        message: str,
        data: Dict = None
    ) -> Dict:
        """
        Invoke notification sender Lambda asynchronously
        
        Args:
            notification_type: Type of notification
            user_id: User ID
            user_email: User email address
            message: Notification message
            data: Additional data for notification
        
        Returns:
            Invocation result
        """
        if not self.use_lambda or not self.lambda_client:
            print(f"⚠️  Would send {notification_type} notification to user {user_id}")
            return {
                "success": False,
                "message": "Lambda not configured"
            }
        
        try:
            payload = {
                "notification_type": notification_type,
                "user_id": user_id,
                "user_email": user_email,
                "message": message,
                "data": data or {}
            }
            
            response = self.lambda_client.invoke(
                FunctionName='learnloop-notification-sender',
                InvocationType='Event',  # Async invocation
                Payload=json.dumps(payload)
            )
            
            print(f"✅ Lambda invoked for notification: {notification_type}")
            
            return {
                "success": True,
                "request_id": response.get('ResponseMetadata', {}).get('RequestId'),
                "status_code": response['StatusCode']
            }
            
        except Exception as e:
            print(f"❌ Lambda invocation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_lambda_status(self, request_id: str) -> Dict:
        """
        Check status of Lambda invocation (for debugging)
        
        Args:
            request_id: AWS request ID from invocation
        
        Returns:
            Status information
        """
        # Lambda async invocations don't provide direct status checking
        # You would need to use CloudWatch Logs or a callback mechanism
        return {
            "request_id": request_id,
            "message": "Check CloudWatch Logs for execution details"
        }

# Global Lambda service instance
lambda_service = LambdaService()

# Convenience functions
def invoke_material_processor(s3_key: str, user_id: int, material_id: int) -> Dict:
    """Invoke material processor Lambda"""
    return lambda_service.invoke_material_processor(s3_key, user_id, material_id)

def send_notification(
    notification_type: str,
    user_id: int,
    user_email: str,
    message: str,
    data: Dict = None
) -> Dict:
    """Send notification via Lambda"""
    return lambda_service.invoke_notification_sender(
        notification_type, user_id, user_email, message, data
    )

def is_lambda_enabled() -> bool:
    """Check if Lambda is enabled"""
    return lambda_service.use_lambda
