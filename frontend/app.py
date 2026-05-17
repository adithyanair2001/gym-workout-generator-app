"""Flask frontend for Gym Workout RAG System."""
import os
import subprocess
import signal
import requests
import time
import atexit
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Configuration
FASTAPI_URL = "http://localhost:8000"
FASTAPI_PROCESS = None

def start_fastapi_server():
    """Start the FastAPI server and wait for it to be fully ready."""
    global FASTAPI_PROCESS
    
    # Check if already running
    try:
        response = requests.get(f"{FASTAPI_URL}/health", timeout=2)
        health_data = response.json()
        vector_db = health_data.get('vector_db', {})
        if vector_db.get('count', 0) > 0:
            print(f"✅ FastAPI server is already running with {vector_db['count']} exercises loaded")
            return True
        else:
            print("⚠️  FastAPI server is running but vector database is empty")
            print("   Waiting for exercises to be fetched and loaded...")
    except requests.exceptions.RequestException:
        pass
    
    try:
        print("🚀 Starting FastAPI server...")
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        venv_python = os.path.join(backend_dir, 'venv', 'bin', 'python')
        
        # Check if venv python exists
        if not os.path.exists(venv_python):
            print(f"❌ Virtual environment not found at {venv_python}")
            print("Please create a virtual environment first: python -m venv venv")
            return False
        
        # Start FastAPI with output visible in terminal
        FASTAPI_PROCESS = subprocess.Popen(
            [venv_python, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
            cwd=backend_dir,
            preexec_fn=os.setsid if os.name != 'nt' else None  # Create new process group on Unix
        )
        
        # Wait for server to start AND for exercises to be loaded
        print("⏳ Waiting for FastAPI server to initialize...")
        print("   This includes:")
        print("   1. Starting the server")
        print("   2. Fetching exercises from ExerciseDB (if needed)")
        print("   3. Creating embeddings and loading into ChromaDB")
        print("   (This may take 1-2 minutes on first run)")
        
        max_wait = 180  # 3 minutes max wait
        for i in range(max_wait):
            time.sleep(1)
            try:
                response = requests.get(f"{FASTAPI_URL}/health", timeout=2)
                health_data = response.json()
                vector_db = health_data.get('vector_db', {})
                exercise_count = vector_db.get('count', 0)
                
                if exercise_count > 0:
                    print(f"✅ FastAPI server is ready!")
                    print(f"   - Server: {FASTAPI_URL}")
                    print(f"   - Exercises loaded: {exercise_count}")
                    print(f"   - Vector database: {vector_db.get('status', 'unknown')}")
                    return True
                elif i % 15 == 0 and i > 0:
                    print(f"   Still initializing... ({i}s elapsed)")
                    
            except requests.exceptions.RequestException:
                if i % 15 == 0 and i > 0:
                    print(f"   Waiting for server to start... ({i}s elapsed)")
                continue
        
        print("⚠️  Server initialization timeout after 3 minutes.")
        print("   The server may still be starting. Check the terminal output above.")
        return False
        
    except Exception as e:
        print(f"❌ Failed to start FastAPI server: {str(e)}")
        return False

def stop_fastapi_server():
    """Stop the FastAPI server on Flask shutdown."""
    global FASTAPI_PROCESS
    
    if FASTAPI_PROCESS:
        print("\n🛑 Stopping FastAPI server...")
        try:
            if os.name != 'nt':
                # On Unix, kill the entire process group
                os.killpg(os.getpgid(FASTAPI_PROCESS.pid), signal.SIGTERM)
            else:
                # On Windows, just terminate the process
                FASTAPI_PROCESS.terminate()
            
            FASTAPI_PROCESS.wait(timeout=5)
            print("✅ FastAPI server stopped")
        except Exception as e:
            print(f"⚠️  Error stopping FastAPI server: {str(e)}")
        finally:
            FASTAPI_PROCESS = None

# Register cleanup function
atexit.register(stop_fastapi_server)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_workout():
    """Generate workout plan by calling FastAPI backend."""
    try:
        data = request.json
        
        # Prepare user profile - match backend model field names
        user_profile = {
            "height": float(data['height']),
            "weight": float(data['weight']),
            "age": int(data['age']),
            "gender": data['gender'],
            "fitness_level": data['fitness_level'],
            "gym_days_per_week": int(data['days_per_week']),
            "workout_duration_minutes": int(data['session_duration']),
            "goals": [g.strip() for g in data['goals'].split(',')] if isinstance(data['goals'], str) else data['goals'],
            "available_equipment": [e.strip() for e in data['equipment'].split(',')] if isinstance(data['equipment'], str) else data['equipment'],
            "injuries_limitations": [i.strip() for i in data.get('injuries', '').split(',') if i.strip()] if data.get('injuries') else None,
            "preferred_split": data.get('preferred_split', 'full_body')
        }
        
        # Call FastAPI backend
        response = requests.post(
            f"{FASTAPI_URL}/api/v1/generate",
            json=user_profile,
            timeout=600  # 10 minutes timeout for LLM generation (agent needs more time)
        )
        
        if response.status_code == 200:
            return jsonify({
                "success": True,
                "workout_plan": response.json()
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Backend error: {response.text}"
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "message": "Request timeout after 10 minutes. The model may be too slow. Try using a smaller model or LM Studio instead."
        }), 504
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Start FastAPI server before starting Flask
    print("\n" + "=" * 60)
    print("  Gym Workout RAG - Starting Servers")
    print("=" * 60 + "\n")
    
    start_fastapi_server()
    
    print("\n" + "=" * 60)
    print("🌐 Starting Flask frontend server...")
    print(f"📍 Frontend: http://localhost:5000")
    print(f"📍 Backend API: {FASTAPI_URL}")
    print("\n💡 Press Ctrl+C to stop both servers")
    print("=" * 60 + "\n")
    
    try:
        app.run(debug=True, port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down servers...")
        stop_fastapi_server()
        print("✅ Shutdown complete")

# Made with Bob
