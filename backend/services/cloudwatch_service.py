"""
CloudWatch Logging Service
Provides structured logging to CloudWatch or local console
FREE TIER: 5GB logs per month, basic metrics
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

class CloudWatchService:
    """CloudWatch logging service with console fallback"""
    
    def __init__(self, aws_config=None):
        """Initialize CloudWatch service"""
        from aws_config import aws_config as default_config, CLOUDWATCH_LOG_GROUP, CLOUDWATCH_LOG_STREAM, USE_CLOUDWATCH
        
        self.aws_config = aws_config or default_config
        self.log_group = CLOUDWATCH_LOG_GROUP
        self.log_stream = CLOUDWATCH_LOG_STREAM
        self.use_cloudwatch = USE_CLOUDWATCH
        self.cloudwatch_client = self.aws_config.cloudwatch if self.use_cloudwatch else None
        
        # Setup local logging
        self._setup_local_logger()
        
        # Initialize CloudWatch if available
        if self.use_cloudwatch and self.cloudwatch_client:
            self._ensure_log_group_exists()
            self._ensure_log_stream_exists()
    
    def _setup_local_logger(self):
        """Setup local console logger"""
        self.logger = logging.getLogger('LearnLoop')
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _ensure_log_group_exists(self):
        """Create CloudWatch log group if it doesn't exist"""
        if not self.cloudwatch_client:
            return
        
        try:
            self.cloudwatch_client.create_log_group(logGroupName=self.log_group)
            print(f"✅ Created CloudWatch log group: {self.log_group}")
        except self.cloudwatch_client.exceptions.ResourceAlreadyExistsException:
            print(f"✅ CloudWatch log group exists: {self.log_group}")
        except Exception as e:
            print(f"⚠️  Failed to create log group: {e}")
    
    def _ensure_log_stream_exists(self):
        """Create CloudWatch log stream if it doesn't exist"""
        if not self.cloudwatch_client:
            return
        
        try:
            self.cloudwatch_client.create_log_stream(
                logGroupName=self.log_group,
                logStreamName=self.log_stream
            )
            print(f"✅ Created CloudWatch log stream: {self.log_stream}")
        except self.cloudwatch_client.exceptions.ResourceAlreadyExistsException:
            pass  # Stream already exists
        except Exception as e:
            print(f"⚠️  Failed to create log stream: {e}")
    
    def log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Log message to CloudWatch and/or console
        Args:
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            message: Log message
            metadata: Additional metadata to include
        """
        # Prepare log entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        if metadata:
            log_entry.update(metadata)
        
        # Log to console
        log_text = json.dumps(log_entry)
        if level == 'ERROR':
            self.logger.error(log_text)
        elif level == 'WARNING':
            self.logger.warning(log_text)
        elif level == 'DEBUG':
            self.logger.debug(log_text)
        else:
            self.logger.info(log_text)
        
        # Log to CloudWatch if enabled
        if self.use_cloudwatch and self.cloudwatch_client:
            self._send_to_cloudwatch(log_text)
    
    def _send_to_cloudwatch(self, message: str):
        """Send log to CloudWatch"""
        try:
            self.cloudwatch_client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[
                    {
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'message': message
                    }
                ]
            )
        except Exception as e:
            # Don't fail the application if CloudWatch logging fails
            print(f"⚠️  CloudWatch logging failed: {e}")
    
    def log_api_call(self, endpoint: str, method: str, status_code: int, duration_ms: float, user_id: Optional[int] = None):
        """Log API call with metrics"""
        metadata = {
            'type': 'api_call',
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'duration_ms': duration_ms
        }
        if user_id:
            metadata['user_id'] = user_id
        
        self.log('INFO', f"API: {method} {endpoint} - {status_code} ({duration_ms}ms)", metadata)
    
    def log_xp_earned(self, user_id: int, xp_amount: int, reason: str):
        """Log XP earned event"""
        metadata = {
            'type': 'xp_earned',
            'user_id': user_id,
            'xp_amount': xp_amount,
            'reason': reason
        }
        self.log('INFO', f"User {user_id} earned {xp_amount} XP: {reason}", metadata)
    
    def log_error(self, error_type: str, error_message: str, stack_trace: Optional[str] = None):
        """Log error"""
        metadata = {
            'type': 'error',
            'error_type': error_type,
            'error_message': error_message
        }
        if stack_trace:
            metadata['stack_trace'] = stack_trace
        
        self.log('ERROR', f"{error_type}: {error_message}", metadata)

# Global CloudWatch service instance
cloudwatch_service = CloudWatchService()

# Convenience functions
def log_info(message: str, metadata: Optional[Dict[str, Any]] = None):
    """Log info message"""
    cloudwatch_service.log('INFO', message, metadata)

def log_warning(message: str, metadata: Optional[Dict[str, Any]] = None):
    """Log warning message"""
    cloudwatch_service.log('WARNING', message, metadata)

def log_error(message: str, metadata: Optional[Dict[str, Any]] = None):
    """Log error message"""
    cloudwatch_service.log('ERROR', message, metadata)

def log_api_call(endpoint: str, method: str, status_code: int, duration_ms: float, user_id: Optional[int] = None):
    """Log API call"""
    cloudwatch_service.log_api_call(endpoint, method, status_code, duration_ms, user_id)
