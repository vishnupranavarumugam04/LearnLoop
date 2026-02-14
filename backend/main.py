from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os
import socketio

load_dotenv()

# Verify API key is loaded
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    print(f"✅ Gemini API Key loaded: {api_key[:20]}...{api_key[-4:]}")
else:
    print("❌ WARNING: GEMINI_API_KEY not found! Buddy will be in offline mode.")
    print("💡 Add your API key to backend/.env file")

# Initialize database
from database import init_db
init_db()

from api import auth, buddy, graph, material, rooms, health

# Import rate limiting middleware
from middleware.rate_limiter import rate_limit_middleware, rate_limiter

app = FastAPI(title="LearnLoop 2.0 API", description="Backend for LearnLoop AI Learning Companion")

# Socket.IO Setup
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
    ]
)

# Store active users: {socket_id: {user_id, username}}
active_users = {}

@sio.event
async def connect(sid, environ):
    print(f"🔌 Client connected: {sid}")
    print(f"   Connection from: {environ.get('REMOTE_ADDR', 'unknown')}")

@sio.event
async def disconnect(sid):
    if sid in active_users:
        user = active_users.pop(sid)
        print(f"🔌 Client disconnected: {sid} (User: {user.get('username', 'Unknown')})")
        print(f"   👥 Remaining active users: {len(active_users)}")
    else:
        print(f"🔌 Client disconnected: {sid} (unregistered user)")

@sio.event
async def user_connected(sid, data):
    """Register user when they connect"""
    active_users[sid] = {
        'user_id': data.get('user_id'),
        'username': data.get('username')
    }
    print(f"👤 User registered: {data.get('username')} (ID: {data.get('user_id')}, SID: {sid})")
    print(f"   👥 Total active users: {len(active_users)}")
    await sio.emit('connection_confirmed', {'status': 'connected'}, room=sid)

# Make sio available to other modules
app.state.sio = sio
app.state.active_users = active_users

# Configure CORS - Allow both frontend ports (3000 and 3001)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",  # Alternative port in case 3000 is busy
        "https://learnloop-vwnj.vercel.app",
        "https://learnloop-blond.vercel.app",
        "https://*.vercel.app",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware (API Gateway alternative)
@app.middleware("http")
async def add_rate_limiting(request, call_next):
    return await rate_limit_middleware(request, call_next)

# Start rate limiter cleanup task
@app.on_event("startup")
async def startup_event():
    await rate_limiter.start_cleanup_task()
    print("✅ Rate limiter initialized")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(buddy.router, prefix="/api/buddy", tags=["buddy"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(material.router, prefix="/api/material", tags=["material"])
app.include_router(rooms.router, prefix="/api/rooms", tags=["rooms"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
from api import profile, gdpr, analytics, content
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(gdpr.router, prefix="/api/gdpr", tags=["gdpr"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(content.router, prefix="/api/content", tags=["content"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to LearnLoop 2.0 API",
        "status": "running",
        "features": {
            "rate_limiting": "enabled",
            "encryption": "enabled",
            "gdpr_compliance": "enabled",
            "analytics": "enabled",
            "content_providers": "enabled"
        }
    }

# Wrap FastAPI app with Socket.IO
socket_app = socketio.ASGIApp(sio, app)

if __name__ == "__main__":
    uvicorn.run("main:socket_app", host="0.0.0.0", port=8000, reload=True)
