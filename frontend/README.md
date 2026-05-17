# Flask Frontend for Gym Workout RAG

A user-friendly web interface for the Gym Workout RAG backend system.

## Features

- 🎛️ **Server Control**: Start/stop FastAPI backend from the UI
- 📊 **Real-time Status**: Monitor backend server status
- 📝 **User-Friendly Form**: Easy input for user profile details
- 🏋️ **Workout Display**: Beautiful visualization of generated workout plans
- ⚡ **Real-time Generation**: See your workout plan as it's generated

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
pip install -r requirements.txt
```

Or use the backend's virtual environment:

```bash
cd /Users/adithyanair/Desktop/gym-workout-rag-backend
./venv/bin/pip install -r frontend/requirements.txt
```

### 2. Run the Frontend

```bash
# From the frontend directory
python app.py
```

Or using the backend's virtual environment:

```bash
cd /Users/adithyanair/Desktop/gym-workout-rag-backend
./venv/bin/python frontend/app.py
```

### 3. Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

## How to Use

### Step 1: Start the Backend Server

1. Click the **"Start Server"** button in the UI
2. Wait 10-15 seconds for initialization
3. The status indicator will turn green when ready
4. First startup takes longer (fetching 3,000+ exercises)

### Step 2: Fill in Your Profile

Enter your details:
- **Physical**: Height, weight, age, gender
- **Fitness**: Fitness level (beginner/intermediate/advanced)
- **Schedule**: Days per week, session duration
- **Goals**: muscle_gain, weight_loss, strength, endurance
- **Equipment**: barbell, dumbbell, bench, etc.
- **Limitations**: Any injuries or restrictions
- **Split**: Preferred workout split type

### Step 3: Generate Workout

1. Click **"Generate Workout Plan"**
2. Wait 30-60 seconds for AI generation
3. View your personalized workout plan

## Architecture

```
┌─────────────────┐
│  Flask Frontend │  (Port 5000)
│   (This App)    │
└────────┬────────┘
         │ HTTP Requests
         ▼
┌─────────────────┐
│  FastAPI Backend│  (Port 8000)
│   (RAG System)  │
└────────┬────────┘
         │
         ├─► ChromaDB (Vector Store)
         ├─► ExerciseDB API
         └─► MLX LLM (Llama 3.2 3B)
```

## API Endpoints

### Frontend Endpoints

- `GET /` - Main application page
- `GET /api/server/status` - Check backend status
- `POST /api/server/start` - Start backend server
- `POST /api/server/stop` - Stop backend server
- `POST /api/generate` - Generate workout plan

### Backend Endpoints (Proxied)

- `POST /api/v1/generate` - Generate workout plan
- `GET /health` - Backend health check

## Configuration

The frontend automatically connects to:
- **FastAPI Backend**: `http://localhost:8000`
- **Flask Frontend**: `http://localhost:5000`

To change these, edit [`app.py`](app.py:11):

```python
FASTAPI_URL = "http://localhost:8000"  # Backend URL
```

## Troubleshooting

### Backend Won't Start

**Problem**: "Failed to start server"

**Solutions**:
1. Check if port 8000 is already in use
2. Ensure backend dependencies are installed
3. Check backend logs for errors

### Generation Timeout

**Problem**: "Request timeout"

**Solutions**:
1. LLM generation can take 30-60 seconds
2. Check if backend server is running
3. Verify vector database is populated

### Empty Workout Plan

**Problem**: No exercises returned

**Solutions**:
1. Ensure backend server completed initialization
2. Check if vector database has exercises (should be 3,000+)
3. Try different equipment or goals

## Development

### File Structure

```
frontend/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── templates/
    └── index.html        # Main UI template
```

### Adding Features

1. **New Form Fields**: Edit [`templates/index.html`](templates/index.html)
2. **Backend Integration**: Modify [`app.py`](app.py)
3. **Styling**: Update CSS in [`templates/index.html`](templates/index.html)

## Tech Stack

- **Flask 3.0.0** - Web framework
- **Requests 2.31.0** - HTTP client
- **Vanilla JavaScript** - Frontend interactivity
- **CSS3** - Styling and animations

## Notes

- The frontend manages the backend server lifecycle
- First backend startup takes 2-3 minutes (fetching exercises)
- Subsequent startups are faster (~10 seconds)
- LLM generation takes 30-60 seconds per workout plan
- The UI auto-refreshes server status every 5 seconds

## License

Same as the main project.