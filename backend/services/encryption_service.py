"""
Encryption Service for LearnLoop
Provides end-to-end encryption for sensitive data
"""
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import base64
import hashlib

load_dotenv()

class EncryptionService:
    """
    Encryption service using Fernet (symmetric encryption)
    WARNING: Store ENCRYPTION_KEY securely in production (AWS Secrets Manager)
    """
    
    def __init__(self):
        """Initialize encryption service with key from environment"""
        # Get encryption key from environment or generate new one
        encryption_key = os.getenv("ENCRYPTION_KEY")
        
        if not encryption_key:
            # Generate new key if not found (for development only)
            encryption_key = Fernet.generate_key().decode()
            print(f"⚠️  No ENCRYPTION_KEY found in .env")
            print(f"💡 Add this to your .env file:")
            print(f"ENCRYPTION_KEY={encryption_key}")
            print(f"WARNING: This is a NEW key. Data encrypted with old key will be unreadable!")
        
        # Ensure key is in bytes
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        try:
            self.cipher = Fernet(encryption_key)
            print("✅ Encryption service initialized")
        except Exception as e:
            print(f"❌ Encryption initialization failed: {e}")
            print("   Data will be stored unencrypted (INSECURE!)")
            self.cipher = None
    
    def encrypt_text(self, text: str) -> str:
        """
        Encrypt text string
        
        Args:
            text: Plain text to encrypt
        
        Returns:
            Encrypted text (base64 encoded)
        """
        if not self.cipher or not text:
            return text
        
        try:
            encrypted_bytes = self.cipher.encrypt(text.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            print(f"Encryption error: {e}")
            return text  # Fallback to plaintext
    
    def decrypt_text(self, encrypted_text: str) -> str:
        """
        Decrypt text string
        
        Args:
            encrypted_text: Encrypted text (base64 encoded)
        
        Returns:
            Decrypted plain text
        """
        if not self.cipher or not encrypted_text:
            return encrypted_text
        
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_text.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            # If decryption fails, assume it's already plaintext (backwards compatibility)
            print(f"Decryption warning: {e} (data may be unencrypted)")
            return encrypted_text
    
    def encrypt_bytes(self, data: bytes) -> bytes:
        """
        Encrypt binary data (files)
        
        Args:
            data: Binary data to encrypt
        
        Returns:
            Encrypted binary data
        """
        if not self.cipher or not data:
            return data
        
        try:
            return self.cipher.encrypt(data)
        except Exception as e:
            print(f"Encryption error: {e}")
            return data
    
    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt binary data (files)
        
        Args:
            encrypted_data: Encrypted binary data
        
        Returns:
            Decrypted binary data
        """
        if not self.cipher or not encrypted_data:
            return encrypted_data
        
        try:
            return self.cipher.decrypt(encrypted_data)
        except Exception as e:
            print(f"Decryption warning: {e} (data may be unencrypted)")
            return encrypted_data
    
    def hash_data(self, data: str) -> str:
        """
        Create one-way hash of data (for verification, not encryption)
        
        Args:
            data: Data to hash
        
        Returns:
            SHA-256 hash (hex encoded)
        """
        return hashlib.sha256(data.encode()).hexdigest()
    
    def is_encryption_available(self) -> bool:
        """Check if encryption is properly configured"""
        return self.cipher is not None

# Global encryption service instance
encryption_service = EncryptionService()

# Convenience functions
def encrypt_text(text: str) -> str:
    """Encrypt text using global encryption service"""
    return encryption_service.encrypt_text(text)

def decrypt_text(encrypted_text: str) -> str:
    """Decrypt text using global encryption service"""
    return encryption_service.decrypt_text(encrypted_text)

def encrypt_file(file_content: bytes) -> bytes:
    """Encrypt file content using global encryption service"""
    return encryption_service.encrypt_bytes(file_content)

def decrypt_file(encrypted_content: bytes) -> bytes:
    """Decrypt file content using global encryption service"""
    return encryption_service.decrypt_bytes(encrypted_content)

def is_encryption_enabled() -> bool:
    """Check if encryption is enabled"""
    return encryption_service.is_encryption_available()
