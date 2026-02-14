import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "learnloop.db")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with schema"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            level INTEGER DEFAULT 1,
            total_xp INTEGER DEFAULT 0,
            streak_days INTEGER DEFAULT 0,
            last_study_date DATE,
            bio TEXT DEFAULT 'Ready to learn!',
            university TEXT DEFAULT 'LearnLoop University',
            buddy_name TEXT DEFAULT 'Buddy',
            buddy_avatar TEXT DEFAULT 'seedling',
            settings TEXT DEFAULT '{}',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Study sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_type TEXT,
            duration_minutes INTEGER DEFAULT 0,
            xp_earned INTEGER DEFAULT 0,
            concepts_covered TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Knowledge graph nodes - Enhanced for v2.0
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            concept_name TEXT NOT NULL,
            subject TEXT,
            mastery_level INTEGER DEFAULT 0,
            difficulty TEXT DEFAULT 'beginner',
            description TEXT,
            prerequisites TEXT, -- JSON list of concept names
            times_reviewed INTEGER DEFAULT 0,
            first_learned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_reviewed TIMESTAMP,
            next_review_date TIMESTAMP, -- For spaced repetition
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Knowledge graph edges
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            from_concept TEXT,
            to_concept TEXT,
            relationship_type TEXT,
            strength REAL DEFAULT 0.5,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Study Materials (New)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            file_type TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            summary TEXT,
            full_text TEXT,
            learning_stage TEXT DEFAULT 'uploaded', -- 'uploaded', 'buddy_taught', 'user_taught', 'mastered'
            xp_earned_total INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Migration: Add full_text to study_materials
    try:
        cursor.execute("ALTER TABLE study_materials ADD COLUMN full_text TEXT")
    except sqlite3.OperationalError:
        pass

    # Achievements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            achievement_type TEXT,
            achievement_name TEXT,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Chat Sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Chat history (Modified with session_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
    ''')

    # Migration: Add session_id to chat_history if missing
    try:
        cursor.execute("ALTER TABLE chat_history ADD COLUMN session_id INTEGER")
    except sqlite3.OperationalError:
        pass

    # Migration: Add missing columns if they don't exist
    try:
        cursor.execute("ALTER TABLE knowledge_nodes ADD COLUMN difficulty TEXT DEFAULT 'beginner'")
    except sqlite3.OperationalError:
        pass # Column exists
        
    try:
        cursor.execute("ALTER TABLE knowledge_nodes ADD COLUMN description TEXT")
    except sqlite3.OperationalError:
        pass
        
    # Study Rooms (Persistent)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject TEXT,
            creator_id INTEGER NOT NULL,
            creator_name TEXT,
            meeting_link TEXT,
            max_participants INTEGER DEFAULT 10,
            room_type TEXT DEFAULT 'Focus',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creator_id) REFERENCES users(id)
        )
    ''')
    
    # Migrations for study_rooms
    try:
        cursor.execute("ALTER TABLE study_rooms ADD COLUMN meeting_link TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE study_rooms ADD COLUMN creator_name TEXT")
    except sqlite3.OperationalError: pass

    # Room Participants
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS room_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES study_rooms(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Room Messages (Persistent Chat)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS room_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER, -- Null for System/AI messages if desired, or use special ID
            user_name TEXT, -- Cache name for easier display
            content TEXT,
            is_ai BOOLEAN DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES study_rooms(id)
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE knowledge_nodes ADD COLUMN prerequisites TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE knowledge_nodes ADD COLUMN next_review_date TIMESTAMP")
    except sqlite3.OperationalError:
        pass
    
    # Migration: Add learning_stage and xp_earned_total to study_materials
    try:
        cursor.execute("ALTER TABLE study_materials ADD COLUMN learning_stage TEXT DEFAULT 'uploaded'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE study_materials ADD COLUMN xp_earned_total INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
        
    # Migration for user_profiles (v2.0+)
    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN bio TEXT DEFAULT 'Ready to learn!'")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN university TEXT DEFAULT 'LearnLoop University'")
    except sqlite3.OperationalError: pass
        
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

# User operations
def create_user(username: str, password_hash: str, full_name: str = None):
    """Create a new user"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, full_name) VALUES (?, ?, ?)",
            (username, password_hash, full_name)
        )
        user_id = cursor.lastrowid
        
        # Create profile
        cursor.execute(
            "INSERT INTO user_profiles (user_id) VALUES (?)",
            (user_id,)
        )
        
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_username(username: str):
    """Get user by username"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_profile(user_id: int):
    """Get user profile with XP, level, etc."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.*, p.level, p.total_xp, p.streak_days, p.last_study_date,
               p.bio, p.university, p.buddy_name, p.buddy_avatar, p.settings
        FROM users u
        LEFT JOIN user_profiles p ON u.id = p.user_id
        WHERE u.id = ?
    """, (user_id,))
    profile = cursor.fetchone()
    conn.close()
    
    if profile:
        result = dict(profile)
        result['settings'] = json.loads(result.get('settings', '{}'))
        return result
    return None

def get_user_percentile(user_id: int):
    """Calculate what percentile the user is in based on total XP"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all user XPs
    cursor.execute("SELECT user_id, total_xp FROM user_profiles ORDER BY total_xp DESC")
    all_users = cursor.fetchall()
    total_users = len(all_users)
    
    if total_users <= 1:
        conn.close()
        return 1 # Top 1% if only one user
        
    # Find user's rank
    rank = 1
    user_xp = 0
    for i, row in enumerate(all_users):
        if row['user_id'] == user_id:
            rank = i + 1
            user_xp = row['total_xp']
            break
            
    # Percentile = (Rank / Total) * 100
    # For "Top X%", we want the percentage of users at or above this XP
    percentile = max(1, int((rank / total_users) * 100))
    
    conn.close()
    return percentile

def update_xp(user_id: int, xp_amount: int, reason: str = ""):
    """Add XP to user and check for level up, and update streak"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get current stats
    cursor.execute("SELECT total_xp, level, streak_days, last_study_date FROM user_profiles WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    current_xp = row['total_xp']
    current_level = row['level']
    current_streak = row['streak_days']
    last_study_date_str = row['last_study_date']
    
    new_xp = current_xp + xp_amount
    
    # 1. Calculate new level - Linear formula to support up to 1000 levels
    # Each level requires 100 XP: Level = 1 + (XP // 100), capped at 1000
    import math
    new_level = min(1 + (new_xp // 100), 1000)  # Cap at level 1000
    leveled_up = new_level > current_level
    
    # 2. Calculate new streak
    new_streak = current_streak
    from datetime import datetime, timedelta
    now = datetime.now()
    today = now.date()
    
    if last_study_date_str:
        # SQLite stores it as 'YYYY-MM-DD HH:MM:SS' or similar if using CURRENT_TIMESTAMP
        # We only care about the date part
        try:
            last_study_date = datetime.strptime(last_study_date_str.split(' ')[0], '%Y-%m-%d').date()
        except:
            last_study_date = None
            
        if last_study_date:
            if last_study_date == today:
                # Still the same day, no streak change
                pass
            elif last_study_date == today - timedelta(days=1):
                # Studied yesterday! Streak +1
                new_streak += 1
            else:
                # Gap in studying, reset to 1
                new_streak = 1
        else:
            new_streak = 1
    else:
        # First time studying ever
        new_streak = 1
        
    # Update profile
    cursor.execute(
        "UPDATE user_profiles SET total_xp = ?, level = ?, streak_days = ?, last_study_date = CURRENT_TIMESTAMP WHERE user_id = ?",
        (new_xp, new_level, new_streak, user_id)
    )
    
    conn.commit()
    conn.close()
    
    return {
        "new_xp": new_xp,
        "new_level": new_level,
        "leveled_up": leveled_up,
        "xp_gained": xp_amount,
        "new_streak": new_streak
    }

def update_password(user_id: int, new_password_hash: str):
    """Update user password"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (new_password_hash, user_id)
    )
    conn.commit()
    conn.close()
    return True

def verify_user(username: str, password: str):
    """Verify user credentials"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return None
        
    # In a real app we would use bcrypt.checkpw
    # For this v2.0 prototype we are comparing plain text (or simple hash if implemented)
    # The current create_user stores "default_hash" or similar.
    # We should update create_user to store the actual password for this simple auth to work
    
    if user['password_hash'] == password:
        return user
        
    return None

def delete_user(user_id: int):
    """Delete user and all related data"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Delete from all tables
    queries = [
        "DELETE FROM chat_sessions WHERE user_id = ?",
        "DELETE FROM chat_history WHERE user_id = ?", # Assuming this has user_id, if not it's linked via sessions
        "DELETE FROM study_materials WHERE user_id = ?",
        "DELETE FROM knowledge_edges WHERE user_id = ?",
        "DELETE FROM knowledge_nodes WHERE user_id = ?",
        "DELETE FROM study_sessions WHERE user_id = ?",
        "DELETE FROM user_profiles WHERE user_id = ?",
        "DELETE FROM users WHERE id = ?"
    ]
    
    try:
        for query in queries:
            cursor.execute(query, (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def add_knowledge_node(user_id: int, concept_name: str, subject: str = "General", mastery_level: int = 0, description: str = ""):
    """Add a concept to user's knowledge graph"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if already exists
    cursor.execute(
        "SELECT id, mastery_level FROM knowledge_nodes WHERE user_id = ? AND concept_name = ?",
        (user_id, concept_name)
    )
    existing = cursor.fetchone()
    
    if existing:
        # Update last reviewed and potentially mastery
        new_mastery = max(existing['mastery_level'], mastery_level)
        cursor.execute(
            "UPDATE knowledge_nodes SET last_reviewed = CURRENT_TIMESTAMP, times_reviewed = times_reviewed + 1, mastery_level = ?, description = COALESCE(NULLIF(?, ''), description) WHERE id = ?",
            (new_mastery, description, existing['id'])
        )
    else:
        # Create new node
        cursor.execute(
            "INSERT INTO knowledge_nodes (user_id, concept_name, subject, mastery_level, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, concept_name, subject, mastery_level, description)
        )
    
    conn.commit()
    conn.close()

def add_knowledge_edge(user_id: int, from_concept: str, to_concept: str, relationship_type: str = "relates_to", strength: float = 0.5):
    """Add a connection between concepts"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute(
        "SELECT id FROM knowledge_edges WHERE user_id = ? AND from_concept = ? AND to_concept = ?",
        (user_id, from_concept, to_concept)
    )
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO knowledge_edges (user_id, from_concept, to_concept, relationship_type, strength) VALUES (?, ?, ?, ?, ?)",
            (user_id, from_concept, to_concept, relationship_type, strength)
        )
        conn.commit()
    conn.close()

def get_knowledge_graph(user_id: int):
    """Get user's knowledge graph"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get nodes
    cursor.execute(
        "SELECT * FROM knowledge_nodes WHERE user_id = ? ORDER BY first_learned DESC",
        (user_id,)
    )
    nodes = [dict(row) for row in cursor.fetchall()]
    
    # Get edges
    cursor.execute(
        "SELECT * FROM knowledge_edges WHERE user_id = ?",
        (user_id,)
    )
    edges = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {"nodes": nodes, "edges": edges}

def create_chat_session(user_id: int, title: str):
    """Create a new chat session"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_sessions (user_id, title) VALUES (?, ?)",
        (user_id, title)
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_chat_sessions(user_id: int):
    """Get all chat sessions for user"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    )
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sessions

def delete_chat_session(session_id: int):
    """Delete a chat session"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

def save_chat_message(user_id: int, role: str, content: str, session_id: int = None):
    """Save chat message to history"""
    conn = get_db()
    cursor = conn.cursor()
    
    # If no session ID provided, create or use last active? 
    # For now, we assume frontend handles session creation, but if None, we put in null logic or default
    
    cursor.execute(
        "INSERT INTO chat_history (user_id, session_id, role, content) VALUES (?, ?, ?, ?)",
        (user_id, session_id, role, content)
    )
    
    # Update session timestamp
    if session_id:
        cursor.execute(
            "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,)
        )
        
    conn.commit()
    conn.close()

def get_chat_history(user_id: int, limit: int = 50, session_id: int = None):
    """Get recent chat history"""
    conn = get_db()
    cursor = conn.cursor()
    
    if session_id:
        cursor.execute(
            "SELECT role, content, timestamp FROM chat_history WHERE session_id = ? ORDER BY timestamp ASC",
            (session_id,)
        )
    else:
        # Fallback for dashboard preview or legacy
        cursor.execute(
            "SELECT role, content, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        # return reversed to show chronological order
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return list(reversed(messages))
        
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages

def update_user_settings(user_id: int, settings: dict):
    """Update user settings JSON"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Get existing settings
        cursor.execute("SELECT settings FROM user_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        raw_settings = row['settings'] if row else '{}'
        existing_settings = json.loads(raw_settings) if raw_settings else {}
        
        # Merge new settings
        existing_settings.update(settings)
        new_settings_json = json.dumps(existing_settings)
        
        cursor.execute(
            "UPDATE user_profiles SET settings = ? WHERE user_id = ?",
            (new_settings_json, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating settings: {e}")
        return False
    finally:
        conn.close()

def update_material_stage(material_id: int, new_stage: str, xp_to_add: int = 0):
    """Update the learning stage of a material and optionally award XP"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Get user_id for XP update
        cursor.execute("SELECT user_id, xp_earned_total FROM study_materials WHERE id = ?", (material_id,))
        row = cursor.fetchone()
        if not row:
            return False
            
        user_id = row['user_id']
        current_xp_material = row['xp_earned_total']
        
        # Update material
        cursor.execute(
            "UPDATE study_materials SET learning_stage = ?, xp_earned_total = ? WHERE id = ?",
            (new_stage, current_xp_material + xp_to_add, material_id)
        )
        
        conn.commit()
        
        # Award general user XP if applicable
        if xp_to_add > 0:
            update_xp(user_id, xp_to_add, f"material_progress_{new_stage}")
            
        return True
    except Exception as e:
        print(f"Error updating material stage: {e}")
        return False
    finally:
        conn.close()

def update_buddy_profile(user_id: int, buddy_name: str, buddy_avatar: str):
    """Update buddy name and avatar"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE user_profiles SET buddy_name = ?, buddy_avatar = ? WHERE user_id = ?",
            (buddy_name, buddy_avatar, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating buddy profile: {e}")
        return False
    finally:
        conn.close()

def update_user_profile(user_id: int, bio: str = None, university: str = None):
    """Update user bio and university"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        if bio is not None and university is not None:
            cursor.execute(
                "UPDATE user_profiles SET bio = ?, university = ? WHERE user_id = ?",
                (bio, university, user_id)
            )
        elif bio is not None:
            cursor.execute(
                "UPDATE user_profiles SET bio = ? WHERE user_id = ?",
                (bio, user_id)
            )
        elif university is not None:
            cursor.execute(
                "UPDATE user_profiles SET university = ? WHERE user_id = ?",
                (university, user_id)
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return False
    finally:
        conn.close()

def get_material_by_filename(user_id: int, filename: str):
    """Get material by user and filename"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM study_materials WHERE user_id = ? AND filename = ?", (user_id, filename))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_material_by_id(material_id: int):
    """Get material by its ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM study_materials WHERE id = ?", (material_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_study_material(material_id: int):
    """Delete a study material and its associated data"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM study_materials WHERE id = ?", (material_id,))
        # Also clean up associated chat history or knowledge nodes if desired
        # cursor.execute("DELETE FROM chat_history WHERE material_id = ?", (material_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting material: {e}")
        return False
    finally:
        conn.close()

# Initialize database on import
if not os.path.exists(DB_PATH):
    init_db()
else:
    # Always run init to check for migrations
    init_db()
