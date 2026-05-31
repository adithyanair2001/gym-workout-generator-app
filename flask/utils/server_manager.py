"""
Server Manager for FastAPI Backend
Handles starting, stopping, and monitoring the FastAPI server
"""

import os
import subprocess
import signal
import requests
import time
import atexit


class ServerManager:
    """Manages the FastAPI backend server lifecycle."""
    
    def __init__(self, fastapi_url="http://localhost:7501"):
        """
        Initialize the server manager.
        
        Args:
            fastapi_url: Base URL for the FastAPI server
        """
        self.fastapi_url = fastapi_url
        self.process = None
        
        # Register cleanup on exit
        atexit.register(self.stop_server)
    
    def is_server_running(self):
        """
        Check if the FastAPI server is running and healthy.
        
        Returns:
            tuple: (is_running: bool, exercise_count: int)
        """
        try:
            response = requests.get(f"{self.fastapi_url}/health", timeout=2)
            health_data = response.json()
            vector_db = health_data.get('vector_db', {})
            exercise_count = vector_db.get('count', 0)
            return True, exercise_count
        except requests.exceptions.RequestException:
            return False, 0
    
    def start_server(self, max_wait=180):
        """
        Start the FastAPI server and wait for it to be fully ready.
        
        Args:
            max_wait: Maximum seconds to wait for server initialization
            
        Returns:
            bool: True if server started successfully, False otherwise
        """
        # Check if already running
        is_running, exercise_count = self.is_server_running()
        if is_running:
            if exercise_count > 0:
                print(f"✅ FastAPI server is already running with {exercise_count} exercises loaded")
                return True
            else:
                print("⚠️  FastAPI server is running but vector database is empty")
                print("   Waiting for exercises to be fetched and loaded...")
        
        try:
            print("🚀 Starting FastAPI server...")
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            venv_python = os.path.join(backend_dir, 'venv', 'bin', 'python')
            
            # Check if venv python exists
            if not os.path.exists(venv_python):
                print(f"❌ Virtual environment not found at {venv_python}")
                print("Please create a virtual environment first: python -m venv venv")
                return False
            
            # Start FastAPI with output visible in terminal
            self.process = subprocess.Popen(
                [venv_python, '-m', 'uvicorn', 'fastapiserver.main:app',
                 '--host', '0.0.0.0', '--port', '7501'],
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
            
            for i in range(max_wait):
                time.sleep(1)
                is_running, exercise_count = self.is_server_running()
                
                if is_running and exercise_count > 0:
                    print(f"✅ FastAPI server is ready!")
                    print(f"   - Server: {self.fastapi_url}")
                    print(f"   - Exercises loaded: {exercise_count}")
                    return True
                elif i % 15 == 0 and i > 0:
                    status = "initializing" if is_running else "starting"
                    print(f"   Still {status}... ({i}s elapsed)")
            
            print(f"⚠️  Server initialization timeout after {max_wait} seconds.")
            print("   The server may still be starting. Check the terminal output above.")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start FastAPI server: {str(e)}")
            return False
    
    def stop_server(self):
        """Stop the FastAPI server."""
        if self.process:
            print("\n🛑 Stopping FastAPI server...")
            try:
                if os.name != 'nt':
                    # On Unix, kill the entire process group
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    # On Windows, just terminate the process
                    self.process.terminate()
                
                self.process.wait(timeout=5)
                print("✅ FastAPI server stopped")
            except Exception as e:
                print(f"⚠️  Error stopping FastAPI server: {str(e)}")
            finally:
                self.process = None
    
    def get_server_status(self):
        """
        Get detailed server status.
        
        Returns:
            dict: Server status information
        """
        try:
            response = requests.get(f"{self.fastapi_url}/health", timeout=2)
            return {
                "running": True,
                "health": response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                "running": False,
                "error": str(e)
            }

# Made with Bob
