"""
AWS Setup Script - Create S3 Bucket and Configure
Run this script ONCE to set up your AWS infrastructure
"""
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "learnloop-materials")

def main():
    """Setup AWS infrastructure"""
    print("🚀 Starting AWS Setup for LearnLoop")
    print(f"   Region: {AWS_REGION}")
    print(f"   Bucket: {S3_BUCKET_NAME}")
    
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        print("❌ AWS credentials not found in .env file")
        print("   Please add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to backend/.env")
        return False
    
    # Create S3 client
    try:
        s3_client = boto3.client(
            's3',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        print("✅ AWS S3 client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize S3 client: {e}")
        return False
    
    # Create S3 bucket
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        print(f"✅ S3 bucket '{S3_BUCKET_NAME}' already exists")
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code == '404':
            print(f"📦 Creating S3 bucket: {S3_BUCKET_NAME}")
            try:
                if AWS_REGION == 'us-east-1':
                    s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
                else:
                    s3_client.create_bucket(
                        Bucket=S3_BUCKET_NAME,
                        CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                    )
                print(f"✅ Created S3 bucket: {S3_BUCKET_NAME}")
            except Exception as create_error:
                print(f"❌ Failed to create bucket: {create_error}")
                return False
        else:
            print(f"❌ Bucket check failed: {e}")
            return False
    
    # Configure CORS
    cors_configuration = {
        'CORSRules': [{
            'AllowedHeaders': ['*'],
            'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
            'AllowedOrigins': ['http://localhost:3000', 'http://localhost:8000'],
            'ExposeHeaders': ['ETag'],
            'MaxAgeSeconds': 3000
        }]
    }
    
    try:
        s3_client.put_bucket_cors(
            Bucket=S3_BUCKET_NAME,
            CORSConfiguration=cors_configuration
        )
        print("✅ S3 CORS configured for frontend uploads")
    except Exception as e:
        print(f"⚠️  CORS configuration failed: {e}")
    
    # Create CloudWatch log group
    try:
        cloudwatch_client = boto3.client(
            'logs',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        log_group = os.getenv("CLOUDWATCH_LOG_GROUP", "/aws/learnloop/backend")
        
        try:
            cloudwatch_client.create_log_group(logGroupName=log_group)
            print(f"✅ Created CloudWatch log group: {log_group}")
        except cloudwatch_client.exceptions.ResourceAlreadyExistsException:
            print(f"✅ CloudWatch log group already exists: {log_group}")
        
    except Exception as e:
        print(f"⚠️  CloudWatch setup failed: {e}")
    
    # Test Bedrock access (optional)
    try:
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        print("✅ Bedrock client initialized")
        print("   Note: You may need to request model access in AWS Console")
        print("   https://console.aws.amazon.com/bedrock/home#/modelaccess")
    except Exception as e:
        print(f"⚠️  Bedrock not available: {e}")
        print("   This is optional. Request access if you want to use AWS AI models")
    
    print("\n" + "="*60)
    print("🎉 AWS Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Update backend/.env with:")
    print("   USE_S3=true")
    print("   USE_CLOUDWATCH=true")
    print("   USE_BEDROCK=true (optional, if you have Bedrock access)")
    print("\n2. Restart the LearnLoop backend")
    print("\n3. Upload a material to test S3 integration")
    print("\n" + "="*60)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
