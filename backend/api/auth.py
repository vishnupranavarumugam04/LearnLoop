from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import create_user, get_user_by_username, verify_user
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter()

# Security Config
SECRET_KEY = "your-secret-key-should-be-in-env" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def verify_password(plain_password, hashed_password):
    """Verify password with proper error handling"""
    try:
        # passlib handles encoding internally, just pass the string
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Password verification error: {e}")
        # Fallback for plain text comparison (dev mode backwards compatibility)
        try:
            return str(hashed_password) == str(plain_password)
        except:
            return False

def get_password_hash(password):
    """Hash password - passlib handles encoding internally"""
    try:
        # Ensure it's a string, passlib handles the rest
        if isinstance(password, bytes):
            password = password.decode('utf-8')
        return pwd_context.hash(str(password))
    except Exception as e:
        print(f"Password hashing error: {e}")
        # Fallback: return plaintext (dev only - NOT for production!)
        return str(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Models
class UserRegister(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None

class User(BaseModel):
    username: str
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register")
async def register(user: UserRegister):
    print(f"🔍 Registration attempt: username={user.username}, full_name={user.full_name}")
    
    existing = get_user_by_username(user.username)
    if existing:
        print(f"❌ User already exists: {user.username}")
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_pw = get_password_hash(user.password)
    user_id = create_user(user.username, hashed_pw, user.full_name)
    
    if not user_id:
        print(f"❌ Failed to create user: {user.username}")
        raise HTTPException(status_code=500, detail="Failed to create user")
    
    print(f"✅ User created successfully: {user.username} (ID: {user_id})")
    return {"id": user_id, "username": user.username, "message": "User created successfully"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # We use OAuth2PasswordRequestForm standard for Swagger UI compatibility
    user = get_user_by_username(form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # Check password - handle both legacy plain text (for dev transition) and bcrypt
    is_valid = False
    stored_pw = user['password_hash']
    
    if verify_password(form_data.password, stored_pw):
        is_valid = True
    elif stored_pw == form_data.password: # Backwards compatibility for dev
        is_valid = True
        
    if not is_valid:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['username'], "user_id": user['id']},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Custom Dependency to get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    from database import get_user_by_username
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

@router.get("/users/me", response_model=User)
async def read_users_me(token: str = "mock-jwt-token"):
    # Mock token decoding
    # If token starts with "user_id:", extract it
    user_id = 1
    username = "student"
    full_name = "Student User"
    
    if token.startswith("user_id:"):
        try:
            uid = int(token.split(":")[1])
            from database import get_user_profile
            # We need a get_user_by_id function or similar
            # For now simplified:
            from database import get_db
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (uid,))
            u = cursor.fetchone()
            conn.close()
            if u:
                return {"username": u["username"], "full_name": u["full_name"]}
        except:
            pass
            
    return {"username": username, "full_name": full_name}

class DeleteUserRequest(BaseModel):
    username: str

@router.delete("/users/me")
async def delete_current_user(username: str):
    from database import get_user_by_username, delete_user
    
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    success = delete_user(user['id'])
    if success:
        return {"status": "success", "message": "Account deleted"}
    else:
         raise HTTPException(status_code=500, detail="Failed to delete account")

class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str

@router.post("/change-password")
async def change_password(req: ChangePasswordRequest):
    # Mock validation of old password (in real app, verify hash)
    # For this demo, we assume old password is "password" for the default user
    # Or just allow any old password for testing per instructions
    
    from database import update_password, get_user_by_username
    
    user = get_user_by_username(req.username)
    if not user:
         raise HTTPException(status_code=404, detail="User not found")
         
    # In real app, hash the new password
    # For now, storing plain text or mock hash
    update_password(user['id'], req.new_password)
    
    return {"status": "success", "message": "Password updated successfully"}
