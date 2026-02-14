from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
import time
import json
import os
import google.generativeai as genai
from database import get_db
import asyncio
import re

router = APIRouter()

# --- Connection Manager for WebSockets ---
class ConnectionManager:
    def __init__(self):
        # Map room_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            # Send JSON string
            json_msg = json.dumps(message)
            # Iterate copy to avoid modification errors
            for connection in self.active_connections[room_id][:]:
                try:
                    await connection.send_text(json_msg)
                except Exception:
                    # Clean up dead connection
                    await self.disconnect(connection, room_id)

manager = ConnectionManager()

# --- Models ---
class CreateRoomRequest(BaseModel):
    name: str
    subject: str
    creator_id: Optional[int] = 1 # Fallback
    creator_name: Optional[str] = "Host"
    meeting_link: Optional[str] = ""
    max_participants: Optional[int] = 10
    type: Optional[str] = "Focus"

# --- Helper Logic ---
async def save_message_to_db(room_id: int, user_id: int, user_name: str, content: str, is_ai: bool = False):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO room_messages (room_id, user_id, user_name, content, is_ai) VALUES (?, ?, ?, ?, ?)",
        (room_id, user_id, user_name, content, is_ai)
    )
    conn.commit()
    conn.close()

async def process_ai_learning(room_id: int, message: str, user_name: str, subject: str, creator_id: int):
    """Background AI analysis to extract knowledge and potentially reply"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or len(message.strip()) < 10: return

    try:
        genai.configure(api_key=api_key)
        # Use a stable model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 1. Broad Knowledge Extraction (Subject + General)
        # We want the Buddy to learn from the conversation.
        prompt = f"""
        You are an AI Buddy observing a chat in a '{subject}' study room.
        User {user_name} said: "{message}"
        
        Extract any educational concepts or facts mentioned. 
        Categorize each as either:
        - 'Subject': Specific to {subject}
        - 'General': Open-world / general knowledge
        
        Format as JSON list: [{{"concept": "...", "type": "Subject"|"General", "description": "..."}}]
        If nothing educational, return empty list [].
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Extract JSON from potential markdown
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            try:
                knowledge_units = json.loads(json_match.group())
                from database import add_knowledge_node, update_xp
                
                for unit in knowledge_units:
                    concept = unit.get('concept')
                    k_type = unit.get('type', 'General')
                    description = unit.get('description', '')
                    
                    if concept:
                        # Map learning to the room creator (fallback) or ideally the contributing user
                        # For now, we contribute development to the room's knowledge pool
                        add_knowledge_node(
                            creator_id, 
                            concept, 
                            subject=subject if k_type == 'Subject' else 'General',
                            mastery_level=20, # Low initial mastery for observation
                            description=f"Leared from Room #{room_id} conversation: {description}"
                        )
                
                # Small XP reward for the room creator when Buddy learns something useful
                if knowledge_units:
                    update_xp(creator_id, 2, "buddy_learning_observation")

            except Exception as e:
                print(f"JSON Parse Error in room learning: {e}")
            
        # 2. Check for Direct Buddy Interaction
        if "buddy" in message.lower() or "ai" in message.lower():
            chat_prompt = f"""
            You are Buddy, a helpful AI studying with users in a {subject} room.
            User {user_name} said: "{message}"
            Keep your reply concise and encouraging.
            """
            chat_response = model.generate_content(chat_prompt)
            reply = chat_response.text.strip()
            
            await save_message_to_db(room_id, 0, "Buddy AI", reply, True)
            await manager.broadcast({
                "user_name": "Buddy AI",
                "content": reply,
                "is_ai": True,
                "timestamp": int(time.time() * 1000)
            }, str(room_id))

    except Exception as e:
        print(f"AI Room Learning Error: {e}")

# --- REST Endpoints ---

@router.post("/")
async def create_room(request: CreateRoomRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO study_rooms (name, subject, creator_id, creator_name, meeting_link, max_participants, room_type, is_active) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (request.name, request.subject, request.creator_id, request.creator_name, request.meeting_link, request.max_participants, request.type, 1)
    )
    room_id = cursor.lastrowid
    
    # Add creator as participant
    cursor.execute(
        "INSERT INTO room_participants (room_id, user_id) VALUES (?, ?)",
        (room_id, request.creator_id)
    )
    
    # Initial system message
    cursor.execute(
        "INSERT INTO room_messages (room_id, user_name, content, is_ai) VALUES (?, ?, ?, ?)",
        (room_id, "Buddy AI", f"Welcome to the {request.subject} room! I'm listening.", 1)
    )
    
    conn.commit()
    conn.close()
    
    return {"id": room_id, "message": "Room created"}

@router.get("/")
async def get_rooms():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM study_rooms WHERE is_active = 1 ORDER BY created_at DESC")
    rooms_data = [dict(row) for row in cursor.fetchall()]
    
    rooms = []
    for room in rooms_data:
        cursor.execute("""
            SELECT u.username 
            FROM room_participants rp
            JOIN users u ON rp.user_id = u.id
            WHERE rp.room_id = ?
        """, (room['id'],))
        participants = [row['username'] for row in cursor.fetchall()]
        rooms.append({**room, "participants": participants})
        
    conn.close()
    return rooms

@router.get("/{room_id}")
async def get_room_details(room_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    # Room info
    cursor.execute("SELECT * FROM study_rooms WHERE id = ?", (room_id,))
    room = cursor.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="Room not found")
        
    # Participants
    cursor.execute("""
        SELECT u.username, u.id 
        FROM room_participants rp
        JOIN users u ON rp.user_id = u.id
        WHERE rp.room_id = ?
    """, (room_id,))
    participants = [row['username'] for row in cursor.fetchall()]
    
    # Recent messages
    cursor.execute("SELECT user_name, content, is_ai, timestamp FROM room_messages WHERE room_id = ? ORDER BY timestamp ASC LIMIT 50", (room_id,))
    messages = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        **dict(room),
        "participants": participants,
        "messages": messages
    }

@router.post("/{room_id}/join")
async def join_room(room_id: int, user_id: int = 1): # Hardcoded user_id fallback for dev
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute("SELECT id FROM study_rooms WHERE id = ?", (room_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Room not found")
        
    # Check if already joined
    cursor.execute("SELECT id FROM room_participants WHERE room_id = ? AND user_id = ?", (room_id, user_id))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO room_participants (room_id, user_id) VALUES (?, ?)", (room_id, user_id))
        conn.commit()
        
    conn.close()
    return {"status": "joined"}

@router.delete("/{room_id}")
async def delete_room(room_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE study_rooms SET is_active = 0 WHERE id = ?", (room_id,))
    conn.commit()
    conn.close()
    return {"status": "room deleted"}

# --- WebSocket Endpoint ---
@router.websocket("/ws/{room_id}/{user_name}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_name: str):
    await manager.connect(websocket, room_id)
    try:
        # Fetch room subject for AI context
        # (Optimized: In real app, cache this. Here, we query DB once per socket start or pass in params)
        # We'll just assume "General" if DB query fails to keep socket fast, but better to query.
        subject = "General" 
        
        while True:
            data = await websocket.receive_text()
            # data expected just to be content text for now
            message_content = data 
            
            # 1. Save to DB
            # We need a user_id. For now, we assume 0 or look it up. 
            # In "Proper" auth, we'd decode token.
            await save_message_to_db(int(room_id), 0, user_name, message_content)
            
            # 2. Broadcast to others
            msg_obj = {
                "user_name": user_name,
                "content": message_content,
                "is_ai": False,
                "timestamp": int(time.time() * 1000)
            }
            await manager.broadcast(msg_obj, room_id)
            
            # 3. Trigger AI (Fire and forget task)
            # In a "Proper" app, we'd fetch the room's subject and creator_id.
            # For simplicity in this demo, we assume the room still exists.
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT subject, creator_id FROM study_rooms WHERE id = ?", (int(room_id),))
            room_info = cursor.fetchone()
            conn.close()
            
            if room_info:
                asyncio.create_task(process_ai_learning(
                    int(room_id), 
                    message_content, 
                    user_name, 
                    room_info['subject'], 
                    room_info['creator_id']
                ))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast({"user_name": "System", "content": f"{user_name} left.", "is_ai": True}, room_id)
