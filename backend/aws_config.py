"""
AWS Configuration Module for LearnLoop
Handles all AWS service client initialization with Free Tier optimization
"""
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

load_dotenv()

# Feature flags - AWS services are OPTIONAL
USE_DYNAMODB = os.getenv("USE_DYNAMODB", "false").lower() == "true"
USE_S3 = os.getenv("USE_S3", "false").lower() == "true"
USE_BEDROCK = os.getenv("USE_BEDROCK", "false").lower() == "true"
USE_CLOUDWATCH = os.getenv("USE_CLOUDWATCH", "false").lower() == "true"

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# DynamoDB Configuration (Free Tier: 25GB storage, 25 RCU/WCU)
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "learnloop-main")
DYNAMODB_MATERIALS_TABLE = os.getenv("DYNAMODB_MATERIALS_TABLE", "learnloop-materials")

# S3 Configuration (Free Tier: 5GB storage, 20k GET, 2k PUT/month)
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "learnloop-materials")

# Bedrock Configuration (Pay per use, but can use efficient models)
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")  # Cheapest Claude model
BEDROCK_EMBEDDING_MODEL = os.getenv("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v1")

# CloudWatch Configuration (Free Tier: 5GB logs, basic metrics)
CLOUDWATCH_LOG_GROUP = os.getenv("CLOUDWATCH_LOG_GROUP", "/aws/learnloop/backend")
CLOUDWATCH_LOG_STREAM = os.getenv("CLOUDWATCH_LOG_STREAM", "api-logs")

class AWSConfig:
    """
    AWS Configuration and Client Manager
    Gracefully handles missing credentials and provides fallback
    """
    
    def __init__(self):
        self.aws_available = self._check_credentials()
        self._dynamodb = None
        self._dynamodb_resource = None
        self._s3 = None
        self._bedrock_runtime = None
        self._cloudwatch = None
        
    def _check_credentials(self) -> bool:
        """Check if AWS credentials are available"""
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            print("ℹ️  AWS credentials not found. Running in local mode (SQLite + local files)")
            return False
        return True
    
    @property
    def dynamodb(self):
        """Get DynamoDB client (lazy initialization)"""
        if not USE_DYNAMODB or not self.aws_available:
            return None
        
        if not self._dynamodb:
            try:
                self._dynamodb = boto3.client(
                    'dynamodb',
                    region_name=AWS_REGION,
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                )
                print("✅ DynamoDB client initialized")
            except Exception as e:
                print(f"⚠️  DynamoDB initialization failed: {e}")
                return None
        return self._dynamodb
    
    @property
    def dynamodb_resource(self):
        """Get DynamoDB resource (for easier table operations)"""
        if not USE_DYNAMODB or not self.aws_available:
            return None
        
        if not self._dynamodb_resource:
            try:
                self._dynamodb_resource = boto3.resource(
                    'dynamodb',
                    region_name=AWS_REGION,
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                )
                print("✅ DynamoDB resource initialized")
            except Exception as e:
                print(f"⚠️  DynamoDB resource initialization failed: {e}")
                return None
        return self._dynamodb_resource
    
    @property
    def s3(self):
        """Get S3 client (lazy initialization)"""
        if not USE_S3 or not self.aws_available:
            return None
        
        if not self._s3:
            try:
                self._s3 = boto3.client(
                    's3',
                    region_name=AWS_REGION,
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                )
                print("✅ S3 client initialized")
            except Exception as e:
                print(f"⚠️  S3 initialization failed: {e}")
                return None
        return self._s3
    
    @property
    def bedrock_runtime(self):
        """Get Bedrock Runtime client (lazy initialization)"""
        if not USE_BEDROCK or not self.aws_available:
            return None
        
        if not self._bedrock_runtime:
            try:
                self._bedrock_runtime = boto3.client(
                    'bedrock-runtime',
                    region_name=AWS_REGION,
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                )
                print("✅ Bedrock Runtime client initialized")
            except Exception as e:
                print(f"⚠️  Bedrock initialization failed: {e}")
                print(f"   Note: Bedrock may require special access. Request access in AWS Console.")
                return None
        return self._bedrock_runtime
    
    @property
    def cloudwatch(self):
        """Get CloudWatch Logs client (lazy initialization)"""
        if not USE_CLOUDWATCH or not self.aws_available:
            return None
        
        if not self._cloudwatch:
            try:
                self._cloudwatch = boto3.client(
                    'logs',
                    region_name=AWS_REGION,
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                )
                print("✅ CloudWatch Logs client initialized")
            except Exception as e:
                print(f"⚠️  CloudWatch initialization failed: {e}")
                return None
        return self._cloudwatch

# Global AWS configuration instance
aws_config = AWSConfig()

# Convenience functions
def get_dynamodb_client():
    """Get DynamoDB client if available"""
    return aws_config.dynamodb

def get_dynamodb_resource():
    """Get DynamoDB resource if available"""
    return aws_config.dynamodb_resource

def get_s3_client():
    """Get S3 client if available"""
    return aws_config.s3

def get_bedrock_client():
    """Get Bedrock client if available"""
    return aws_config.bedrock_runtime

def get_cloudwatch_client():
    """Get CloudWatch client if available"""
    return aws_config.cloudwatch

def is_aws_available() -> bool:
    """Check if AWS services are available"""
    return aws_config.aws_available
