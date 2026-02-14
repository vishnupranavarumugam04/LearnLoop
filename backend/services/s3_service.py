"""
S3 Service - File Storage Service
Provides file upload/download with S3 or local filesystem fallback
FREE TIER: 5GB storage, 20k GET requests, 2k PUT requests per month
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from botocore.exceptions import ClientError

class S3Service:
    """S3 file storage service with local fallback"""
    
    def __init__(self, aws_config=None):
        """Initialize S3 service"""
        from aws_config import aws_config as default_config, S3_BUCKET_NAME, USE_S3
        
        self.aws_config = aws_config or default_config
        self.bucket_name = S3_BUCKET_NAME
        self.use_s3 = USE_S3
        self.s3_client = self.aws_config.s3 if self.use_s3 else None
        
        # Local storage fallback
        self.local_storage_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
        os.makedirs(self.local_storage_path, exist_ok=True)
        
        if self.use_s3 and self.s3_client:
            self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create S3 bucket if it doesn't exist"""
        if not self.s3_client:
            return
        
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ S3 bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    from aws_config import AWS_REGION
                    if AWS_REGION == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                        )
                    print(f"✅ Created S3 bucket: {self.bucket_name}")
                    
                    # Configure CORS for frontend uploads
                    self._configure_cors()
                except Exception as create_error:
                    print(f"⚠️  Failed to create S3 bucket: {create_error}")
            else:
                print(f"⚠️  S3 bucket check failed: {e}")
    
    def _configure_cors(self):
        """Configure CORS for S3 bucket"""
        if not self.s3_client:
            return
        
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
            self.s3_client.put_bucket_cors(
                Bucket=self.bucket_name,
                CORSConfiguration=cors_configuration
            )
            print("✅ S3 CORS configured")
        except Exception as e:
            print(f"⚠️  Failed to configure CORS: {e}")
    
    def upload_file(self, file_content: bytes, filename: str, user_id: int) -> Tuple[str, str]:
        """
        Upload file to S3 or local storage
        Returns: (file_key, file_url)
        """
        # Generate unique file key
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_key = f"materials/user_{user_id}/{timestamp}_{unique_id}_{filename}"
        
        if self.use_s3 and self.s3_client:
            return self._upload_to_s3(file_content, file_key, filename)
        else:
            return self._upload_to_local(file_content, file_key, filename, user_id)
    
    def _upload_to_s3(self, file_content: bytes, file_key: str, filename: str) -> Tuple[str, str]:
        """Upload file to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                ContentType=self._get_content_type(filename),
                Metadata={
                    'original_filename': filename,
                    'upload_timestamp': datetime.now().isoformat()
                }
            )
            
            # Generate URL (presigned for security)
            file_url = f"s3://{self.bucket_name}/{file_key}"
            print(f"✅ Uploaded to S3: {file_key}")
            return file_key, file_url
            
        except ClientError as e:
            print(f"❌ S3 upload failed: {e}")
            # Fallback to local
            return self._upload_to_local(file_content, file_key, filename, user_id="fallback")
    
    def _upload_to_local(self, file_content: bytes, file_key: str, filename: str, user_id) -> Tuple[str, str]:
        """Upload file to local filesystem"""
        # Create user directory
        user_dir = os.path.join(self.local_storage_path, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        
        # Save file
        local_path = os.path.join(user_dir, filename)
        with open(local_path, 'wb') as f:
            f.write(file_content)
        
        print(f"✅ Uploaded to local storage: {local_path}")
        return file_key, local_path
    
    def get_presigned_url(self, file_key: str, expiration: int = 3600) -> str:
        """
        Generate presigned URL for file access
        Args:
            file_key: S3 key or local file path
            expiration: URL expiration in seconds (default 1 hour)
        Returns:
            Presigned URL or local file path
        """
        if self.use_s3 and self.s3_client:
            try:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': file_key},
                    ExpiresIn=expiration
                )
                return url
            except ClientError as e:
                print(f"⚠️  Failed to generate presigned URL: {e}")
                return ""
        else:
            # For local files, return the file path or a local URL
            # In production, you might serve these through FastAPI's static files
            return file_key
    
    def delete_file(self, file_key: str) -> bool:
        """Delete file from S3 or local storage"""
        if self.use_s3 and self.s3_client:
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
                print(f"✅ Deleted from S3: {file_key}")
                return True
            except ClientError as e:
                print(f"❌ S3 delete failed: {e}")
                return False
        else:
            # Delete from local storage
            try:
                if os.path.exists(file_key):
                    os.remove(file_key)
                    print(f"✅ Deleted from local storage: {file_key}")
                    return True
            except Exception as e:
                print(f"❌ Local delete failed: {e}")
                return False
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        extension = filename.lower().split('.')[-1]
        content_types = {
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png'
        }
        return content_types.get(extension, 'application/octet-stream')

# Global S3 service instance
s3_service = S3Service()

# Convenience functions
def upload_file(file_content: bytes, filename: str, user_id: int) -> Tuple[str, str]:
    """Upload file using S3 service"""
    return s3_service.upload_file(file_content, filename, user_id)

def get_presigned_url(file_key: str, expiration: int = 3600) -> str:
    """Get presigned URL for file"""
    return s3_service.get_presigned_url(file_key, expiration)

def delete_file(file_key: str) -> bool:
    """Delete file"""
    return s3_service.delete_file(file_key)
