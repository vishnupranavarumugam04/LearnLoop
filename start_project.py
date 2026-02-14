import subprocess
import time
import webbrowser
import os
import sys
import threading

def stream_output(process, prefix):
    for line in iter(process.stdout.readline, ''):
        print(f"[{prefix}] {line.strip()}")
    process.stdout.close()

def main():
    print("🚀 Starting LearnLoop 2.0...")

    # Get absolute paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")

    # Start Backend
    print("🔌 Starting Backend (FastAPI)...")
    # CRITICAL: Must run socket_app to enable Socket.IO!
    backend_cmd = [sys.executable, "-m", "uvicorn", "main:socket_app", "--reload", "--port", "8000"]
    # We need to run uvicorn from the backend directory to find 'main' module easily or set PYTHONPATH
    # Simpler: run from base but point to backend.main:app ?? No, uvicorn expects module.
    # Let's run inside backend dir.
    
    # Note: On Windows 'sys.executable' is python.
    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=backend_dir,
        stdout=sys.stdout,
        stderr=sys.stderr, # Share console for now, or pipe if we want to prefix
        shell=True # Often needed on windows for resolving paths sometimes, but try without if possible.
        # safe on windows usually.
    )

    # Start Frontend
    print("🎨 Starting Frontend (Next.js)...")
    # Windows: npm.cmd
    npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
    frontend_process = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=frontend_dir,
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=True
    )

    print("⏳ Waiting for services to spin up...")
    time.sleep(5) # Give it a moment

    print("🌐 Opening Browser...")
    webbrowser.open("http://localhost:3000/login")

    try:
        while True:
            time.sleep(1)
            if backend_process.poll() is not None:
                print("Backend exited!")
                break
            if frontend_process.poll() is not None:
                print("Frontend exited!")
                break
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Done.")

if __name__ == "__main__":
    main()
