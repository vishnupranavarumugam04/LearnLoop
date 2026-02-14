import os
import sys

# Path to database
DB_PATH = os.path.join(os.path.dirname(__file__), "learnloop.db")

def reset_db():
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print(f"🗑️ Deleted existing database: {DB_PATH}")
        except PermissionError:
            print("❌ Error: Database is in use. Please stop the running server first!")
            return False
            
    # Re-initialize
    try:
        from database import init_db
        init_db()
        print("✅ Database re-initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

if __name__ == "__main__":
    reset_db()
