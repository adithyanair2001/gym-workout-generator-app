# Gym Workout RAG System

AI-powered personalized workout planner using Retrieval-Augmented Generation (RAG) with ChromaDB vector database and multiple LLM deployment options.

## 🌟 Features

*   **RAG Pipeline**: Retrieves relevant exercises from 1500+ exercises using semantic search
*   **Multiple LLM Options**: MLX, GGUF, LM Studio, OpenAI, Anthropic, Groq
*   **Vector Database**: ChromaDB with sentence-transformers embeddings
*   **Modern Flask Frontend**: Beautiful, responsive UI with gradient design
*   **FastAPI Backend**: High-performance async API with automatic documentation
*   **Scalable Architecture**: Modular design with clear separation of concerns
*   **Persistent Storage**: Vector database persists between restarts

## 📁 Project Structure

```
gym-workout-rag-backend/
├── flask/              # Flask frontend application
│   ├── api/           # API routes and blueprints
│   ├── static/        # CSS, JS, images
│   ├── templates/     # HTML templates
│   └── utils/         # Server manager and utilities
├── fastapiserver/     # FastAPI backend application
│   ├── models/        # Pydantic models
│   ├── services/      # Business logic and LLM services
│   ├── middleware/    # Request ID and other middleware
│   └── utils/         # Utilities and validators
├── data/              # Vector database storage
├── run_frontend.sh    # Startup script (Linux/Mac)
└── run_frontend.bat   # Startup script (Windows)
```

## 🚀 Quick Start

### Choose Your Deployment Method

#### Option 1: Docker (Recommended - No Environment Issues!) 🐳

**Why Docker?**

*   ✅ Works on Windows, Mac, Linux without any setup issues
*   ✅ No Python/venv configuration needed
*   ✅ No ChromaDB C++ build tools required
*   ✅ Consistent environment everywhere
*   ✅ Easy cleanup and updates

**Prerequisites:**

Install Docker for your platform:

| Platform | Recommended option |
|---|---|
| **Windows** | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **macOS (Intel)** | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **macOS (Apple Silicon)** | [Docker Desktop](https://www.docker.com/products/docker-desktop/) **or** [Colima](https://github.com/abiosoft/colima) (lighter-weight) |
| **Linux** | [Docker Engine](https://docs.docker.com/engine/install/) + Docker Compose plugin |

> **macOS — Colima setup (one-time):**
> ```bash
> brew install colima docker docker-compose
> colima start --cpu 4 --memory 6 --network-address
> ```

*   4 GB RAM allocated to Docker
*   ~2 GB disk space for the image

---

**Step 1 — Clone the repository**

```bash
git clone <repo-url>
cd gym-workout-rag-backend
```

**Step 2 — Configure environment**

macOS / Linux:
```bash
cp .env.example .env
```

Windows (Command Prompt):
```cmd
copy .env.example .env
```

Windows (PowerShell):
```powershell
Copy-Item .env.example .env
```

Open `.env` and set at minimum:
```
LLM_BASE_URL=http://host.docker.internal:1234/v1   # LM Studio
LLM_MODEL=local-model
LLM_API_KEY=                                        # leave blank for local servers
```

**Step 3 — Build the image and start services**

```bash
docker compose up --build -d
```

> `docker compose` (v2, no hyphen) is the current standard and ships with Docker Desktop on both Windows and macOS. If you only have the older `docker-compose` (v1) binary, it works too — just replace `docker compose` with `docker-compose` throughout.

**Step 4 — Confirm startup**

```bash
docker compose logs -f
```

Wait until you see both servers ready, then open:

| Service | URL |
|---|---|
| Flask Frontend | http://localhost:7500 |
| FastAPI Backend | http://localhost:7501 |
| API Docs | http://localhost:7501/docs |

> **Note:** Source code is baked into the image at build time. After editing any Python, template, or JS files, re-run `docker compose up --build -d` to pick up the changes.

---

**Important — connecting Docker to LM Studio / OLLAMA / OMLX on your host machine**

Docker containers cannot reach `127.0.0.1` on your host. Use `host.docker.internal` instead, which Docker Desktop resolves automatically on both Windows and macOS. On Linux it is provided via the `extra_hosts` entry already in `docker-compose.yml`.

Set in `.env`:
```
LLM_BASE_URL=http://host.docker.internal:1234/v1   # LM Studio
LLM_BASE_URL=http://host.docker.internal:11434/v1  # OLLAMA
LLM_BASE_URL=http://host.docker.internal:8000/v1   # OMLX
```

Also configure your local server to listen on **all interfaces** (`0.0.0.0`), not just loopback — otherwise the container cannot reach it even with the correct hostname:

*   **LM Studio:** Local Server → Server Options → enable *"Serve on Local Network"*
*   **OMLX:** `omlx serve --host 0.0.0.0 --port 8000 --model <model>`
*   **OLLAMA (macOS/Linux):** `OLLAMA_HOST=0.0.0.0 ollama serve`
*   **OLLAMA (Windows):** set environment variable `OLLAMA_HOST=0.0.0.0` then start Ollama

---

**Common Docker commands**

```bash
# Build (or rebuild after code changes) and start in the background
docker compose up --build -d

# Start without rebuilding (e.g. after only changing .env)
docker compose up -d

# Tail logs (all services)
docker compose logs -f

# Tail logs for the app container only
docker compose logs -f gym-workout-rag

# Stop services — keeps the ChromaDB data volume
docker compose down

# Full reset — removes containers AND data volume
docker compose down -v

# Open a shell inside the running container
docker exec -it gym-workout-rag bash   # macOS / Linux
docker exec -it gym-workout-rag sh     # fallback if bash is unavailable

# Run OLLAMA inside Docker (optional profile)
docker compose --profile with-ollama up --build -d

# Test that the container can reach LM Studio on the host
docker exec -it gym-workout-rag curl http://host.docker.internal:1234/v1/models
```

---

#### Option 2: Traditional Installation (Python/venv)

**Prerequisites:**

*   Python 3.9+
*   **Windows:** Visual C++ Build Tools (for ChromaDB) — or use FAISS as an alternative (see Troubleshooting)
*   **macOS (Apple Silicon):** Supports MLX local models natively
*   **Linux:** All features supported
*   8 GB+ RAM recommended

**Step 1 — Clone the repository**

```bash
git clone <repo-url>
cd gym-workout-rag-backend
```

**Step 2 — Create a virtual environment**

macOS / Linux:
```bash
python -m venv venv
source venv/bin/activate
```

Windows (Command Prompt):
```cmd
python -m venv venv
venv\Scripts\activate
```

Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Step 3 — Install dependencies**

macOS / Linux:
```bash
pip install -r requirements.txt
```

Windows — if ChromaDB fails to build:
```cmd
# Option A: Install Visual C++ Build Tools first, then retry
pip install -r requirements.txt

# Option B: Use FAISS (no C++ compiler needed)
pip install faiss-cpu
pip install -r requirements.txt --no-deps chromadb
```

**Step 4 — Configure environment**

macOS / Linux:
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

Windows (Command Prompt):
```cmd
copy .env.example .env
notepad .env
```

Windows (PowerShell):
```powershell
Copy-Item .env.example .env
notepad .env
```

> **Windows users:**
> *   Set `USE_MLX=false` — MLX is Apple Silicon only
> *   Use forward slashes in file paths: `C:/path/to/model`
> *   Choose GGUF, LM Studio, or a cloud API for your LLM

**Step 5 — Run the application**

macOS / Linux:
```bash
bash run_frontend.sh
```

Windows:
```cmd
run_frontend.bat
```

The application will:

*   Start FastAPI backend on port **7501**
*   Fetch exercises from ExerciseDB (first run only)
*   Create embeddings and load into ChromaDB
*   Start Flask frontend on port **7500**

**Access Points:**

| Service | URL |
|---|---|
| Flask Frontend | http://localhost:7500 |
| FastAPI Backend | http://localhost:7501 |
| API Docs | http://localhost:7501/docs |

## 🎯 LLM Configuration

### Dynamic Model Selection (NEW! ✨)

You can now **select and switch between models directly in the web UI** without restarting the server!

**How it works:**

1.  Open the web UI at http://localhost:7500
2.  Select your preferred model type (MLX, OMLX, GGUF, OpenAI, etc.)
3.  Configure model-specific settings (API keys, model paths, etc.)
4.  Generate workouts - the system uses your selected configuration
5.  Switch models anytime without restarting!

**Benefits:**

*   ✅ No server restart required when changing models
*   ✅ Test different models easily
*   ✅ Per-request model configuration
*   ✅ Service caching for performance
*   ✅ Falls back to `.env` defaults if no model selected

**Legacy Mode:**  
You can still use `.env` file configuration by setting `USE_MLX=true` or `USE_GGUF=true`. When these are enabled, the `.env` settings take precedence over UI selections.

### LLM Deployment Options

### 1\. MLX Local Models (Default) 🍎

**Best for**: Mac users, agent mode with tool calling

```
# .env configuration (optional - can also select in UI)
USE_MLX=false  # Set to false to enable UI selection
MLX_MODEL_PATH=/path/to/mlx-community/Qwen3.5-4B-MLX-4bit
```

**Pros**: Free, private, agent capabilities  
**Cons**: Mac only, slower than cloud APIs

### 2\. OMLX Server 🚀

**Best for**: Mac users wanting OpenAI-compatible API

```
**Note:** OMLX uses port 8000 by default. Our FastAPI server uses port 7501 to avoid conflicts.

# Install and run
pip install omlx
omlx serve --model mlx-community/Qwen3.5-4B-MLX-4bit --port 8000

# .env configuration
USE_MLX=false
LLM_BASE_URL=http://127.0.0.1:8000/v1
```

See [`docs/OMLX_SETUP.md`](docs/OMLX_SETUP.md) for details.

### 3\. GGUF Models 💻

**Best for**: Cross-platform compatibility

```
# .env configuration
USE_GGUF=true
GGUF_MODEL_PATH=/path/to/model.gguf
GGUF_N_CTX=4096
GGUF_N_GPU_LAYERS=0
```

### 4\. Local Servers (LM Studio/OLLAMA) 🖥️

**Best for**: Easy local deployment

```
# .env configuration
USE_MLX=false
LLM_BASE_URL=http://127.0.0.1:1234/v1
```

### 5\. Public APIs (OpenAI/Anthropic/Groq) ☁️

**Best for**: Best quality, fastest inference

```
# .env configuration
USE_MLX=false
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-...
```

## 🎨 Frontend Features

*   **Modern UI**: Beautiful gradient design with smooth animations
*   **Responsive**: Works on desktop, tablet, and mobile
*   **Two-step Workflow**: Model selection → Workout form
*   **Real-time Validation**: Client and server-side validation
*   **Error Handling**: Clear error messages and recovery
*   **Loading States**: Progress indicators during generation

See [`flask/README.md`](flask/README.md) for details.

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```
# LLM Configuration
USE_MLX=true                    # Use MLX models
USE_GGUF=false                  # Use GGUF models
LLM_BASE_URL=http://...         # LLM server URL
LLM_MODEL=gpt-4o-mini          # Model name
LLM_API_KEY=                    # API key (if needed)
LLM_MAX_TOKENS=32000           # Max tokens (for reasoning)

# MLX Configuration
MLX_MODEL_PATH=/path/to/model

# GGUF Configuration
GGUF_MODEL_PATH=/path/to/model.gguf
GGUF_N_CTX=4096
GGUF_N_GPU_LAYERS=0

# ExerciseDB API
EXERCISEDB_API_KEY=your_key_here
```

## 📊 API Endpoints

### FastAPI Backend (Port 8000)

*   `POST /api/v1/generate` - Generate workout plan
*   `GET /health` - Health check with vector DB status

### Flask Frontend (Port 7500)

*   `GET /` - Main application page
*   `POST /api/generate` - Proxy to backend
*   `GET /api/health` - Combined health check

## 🧪 Development

### Running Backend Only

```
python -m uvicorn fastapi.main:app --reload
```

### Running Frontend Only

```
cd flask
python app.py
```

### Project Dependencies

*   **FastAPI**: Backend API framework
*   **Flask**: Frontend web framework
*   **ChromaDB**: Vector database
*   **sentence-transformers**: Embeddings
*   **mlx-lm**: MLX model support (Mac only)
*   **llama-cpp-python**: GGUF model support
*   **openai**: OpenAI API client
*   **httpx**: HTTP client

## 📝 Usage Example

**Start the application**:

**Open browser**: http://localhost:7500

**Select AI model** (Step 1):

*   Choose your preferred model type
*   Configure model settings (informational)

**Fill profile** (Step 2):

*   Height, weight, age, gender
*   Fitness level, goals
*   Available equipment
*   Days per week, session duration

**Generate workout**:

*   Click "Generate Workout Plan"
*   Wait 30-60 seconds
*   View personalized workout plan

## 🐛 Troubleshooting

### LM Studio Issues

#### HTTP 503 Error (Service Unavailable)

**Problem:** Getting 503 errors when trying to connect to LM Studio

**Solutions:**

**Ensure LM Studio Server is Running:**

*   Open LM Studio application
*   Go to "Local Server" tab (left sidebar)
*   Click "Start Server" button
*   Wait for "Server running on port 1234" message
*   Verify server status shows green/active

**Check Model is Loaded:**

*   In LM Studio, go to "Local Server" tab
*   Under "Select a model to load", choose your model
*   Click "Load Model" and wait for it to finish loading
*   Model must be loaded BEFORE making API requests

**Verify Port and URL:**

*   Default LM Studio port is 1234
*   Use `127.0.0.1` not `localhost` (more reliable)

**Test Connection:**

Should return list of loaded models.

**Check Firewall:**

*   Windows Firewall might be blocking the connection
*   Allow LM Studio through Windows Firewall
*   Or temporarily disable firewall to test

#### Model Not Listed / Cannot Select Model

**Problem:** No models appear in LM Studio or model selection doesn't work

**Solutions:**

**Download Models First:**

*   In LM Studio, go to "Discover" tab (🔍 icon)
*   Search for models (e.g., "Llama 3.2 3B", "Qwen 2.5 4B")
*   Click download button
*   Wait for download to complete

**Model Name in .env:**

*   LM Studio doesn't require exact model name
*   Use generic name: `LLM_MODEL=local-model`
*   Or use the model's display name from LM Studio

**Recommended Models for LM Studio:**

*   **Llama 3.2 3B Instruct** (2GB) - Fast, good quality
*   **Qwen 2.5 4B Instruct** (2.5GB) - Better quality
*   **Phi-3 Mini** (2.3GB) - Microsoft, good for instructions
*   Avoid models >7B unless you have 16GB+ RAM

#### Connection Timeout

**Problem:** Requests timeout when generating workouts

**Solutions:**

**Increase Timeout in Frontend:**

*   Edit `flask/static/js/app.js`
*   Find `timeout` setting (usually 60000ms)
*   Increase to 120000ms (2 minutes) or more

**Use Smaller Model:**

*   Larger models (7B+) are slower
*   Switch to 3B-4B models for faster generation

**Reduce Context Length:**

*   In LM Studio settings, reduce "Context Length"
*   Try 2048 or 4096 instead of 8192+

### Docker Issues

#### Container Won't Start

**Check logs:**

```
docker-compose logs gym-workout-rag
```

**Common causes:**

**Port already in use:**

**Docker not running:**

*   Start Docker Desktop (Windows/Mac)
*   Check: `docker ps`

**Out of memory:**

*   Docker Desktop → Settings → Resources
*   Increase memory to at least 4GB

#### Cannot Connect to LM Studio/OLLAMA on Host

**Problem:** Docker container can't reach services running on your computer

**Solution:** Use `host.docker.internal` instead of `localhost`:

```
# ❌ Wrong (won't work in Docker)
LLM_BASE_URL=http://127.0.0.1:1234/v1

# ✅ Correct (works in Docker)
LLM_BASE_URL=http://host.docker.internal:1234/v1
```

**Test from container:**

```
docker exec -it gym-workout-rag curl http://host.docker.internal:1234/v1/models
```

#### Slow Performance in Docker

**Solutions:**

1.  Allocate more resources (Docker Desktop → Settings → Resources)
2.  Use cloud APIs instead of local models
3.  Run OLLAMA inside Docker:

#### Vector Database Issues in Docker

**Clear and rebuild:**

```
docker-compose down
rm -rf data/chroma_db/  # Linux/Mac
rmdir /s /q data\chroma_db  # Windows
docker-compose up -d
```

### Windows-Specific Issues

#### Packages Installing to Temp Folder Instead of venv

**Problem:** When running `pip install -r requirements.txt`, packages install to Windows temp folder instead of the project's venv folder.

**Cause:** Virtual environment is not properly activated before running pip.

**Solution:**

**Use the provided script** (Recommended):

The script now automatically:

*   Creates venv if it doesn't exist
*   Activates venv properly
*   Installs all dependencies in the correct location
*   Verifies installation

**Manual activation** (if needed):

**Verify installation location:**

**Important:** Always activate the venv BEFORE running pip commands. The `(venv)` prefix in your command prompt indicates activation.

#### ChromaDB Installation Fails

**Error:** `Microsoft Visual C++ 14.0 or greater is required`

**Solutions:**

**Install Visual C++ Build Tools** (Recommended)

*   Download: [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
*   Select "Desktop development with C++"
*   Requires ~7GB disk space

**Use Pre-built Wheel:**

**Switch to FAISS** (No C++ needed):

Then modify `fastapiserver/services/vector_store.py` to use FAISS instead of ChromaDB.

#### Port Already in Use (Windows)

```
# Check what's using the port
netstat -ano | findstr :7501

# Kill process (replace PID)
taskkill /PID <PID> /F
```

#### Path Issues (Windows)

Use forward slashes or double backslashes in `.env`:

```
# Good
GGUF_MODEL_PATH=C:/Users/YourName/models/model.gguf

# Also good
GGUF_MODEL_PATH=C:\\Users\\YourName\\models\\model.gguf

# Bad
GGUF_MODEL_PATH=C:\Users\YourName\models\model.gguf
```

### General Issues

#### Backend won't start

**Linux/Mac:**

```
# Check if port is available
lsof -i :7501
kill -9 <PID>
```

**Windows:**

```
netstat -ano | findstr :7501
taskkill /PID <PID> /F
```

#### Frontend connection error

```
# Verify backend is running
curl http://localhost:7501/health
```

#### Slow generation

*   Use smaller model (e.g., 3B-4B instead of 9B+)
*   Try LM Studio or public APIs
*   For GGUF on Windows: Enable GPU acceleration (NVIDIA only)
*   Increase `GGUF_N_GPU_LAYERS` in `.env` (e.g., 30)

#### Vector DB issues

**Linux/Mac:**

```
# Clear and rebuild
rm -rf data/chroma_db/
# Restart application (will refetch exercises)
```

**Windows:**

```
rmdir /s /q data\chroma_db
REM Restart application (will refetch exercises)
```

### ChromaDB Alternatives for Windows

If ChromaDB continues to cause issues, consider these alternatives:

**FAISS** (Recommended)

*   No C++ compilation needed
*   Faster than ChromaDB
*   Pre-built Windows wheels

**Qdrant** (Docker-based)

*   No compilation needed
*   Better for production

**Pinecone** (Cloud, Managed)

*   No local setup
*   Free tier available
*   Best for production

**Weaviate** (Docker-based)

*   No compilation needed
*   GraphQL API

## 📚 API Documentation

### Flask Server API

The Flask frontend provides several API endpoints:

*   **Workout Generation**: `POST /api/generate` - Generate personalized workout plans
*   **Model Validation**: `POST /api/validate-model` - Validate LLM configuration
*   **Health Check**: `GET /api/health` - Check service health
*   **List Models**: `GET /api/models` - List available LLM models

### ExerciseDB Proxy API

The Flask server also provides proxy endpoints to access ExerciseDB:

*   **List Exercises**: `GET /api/exercises?limit=20&cursor=...`
*   **Get Exercise**: `GET /api/exercises/:id`
*   **Search Exercises**: `GET /api/exercises/search?query=bench+press`
*   **Filter by Muscle**: `GET /api/exercises/target/:muscle`
*   **Filter by Body Part**: `GET /api/exercises/bodypart/:part`
*   **Filter by Equipment**: `GET /api/exercises/equipment/:equipment`
*   **List Targets**: `GET /api/exercises/targets`
*   **List Body Parts**: `GET /api/exercises/bodyparts`
*   **List Equipment**: `GET /api/exercises/equipments`

**Note**: ExerciseDB API requires a RapidAPI key. Get yours at: https://rapidapi.com/justin-WFnsXH_t6/api/exercisedb

### Complete Documentation

*   [`flask/README.md`](flask/README.md) - Frontend documentation
*   [`.env.example`](.env.example) - Configuration reference
*   FastAPI Docs: http://localhost:7501/docs (when running)

## 🤝 Contributing

1.  Fork the repository
2.  Create feature branch (`git checkout -b feature/amazing-feature`)
3.  Commit changes (`git commit -m 'Add amazing feature'`)
4.  Push to branch (`git push origin feature/amazing-feature`)
5.  Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 📋 API Response Format

### Custom Workout Plan Format (Android App Compatible)

The API returns workout plans in a custom format designed for Android app integration:

```
{
  "workoutGroups": [
    {
      "groupName": "Day 1: Upper Body Push",
      "isAiGenerated": true,
      "selectedExercises": [
        {
          "exerciseDbId": "EIeI8Vf",
          "exerciseName": "barbell bench press",
          "bodyPart": "Chest",
          "equipments": "Barbell",
          "targetMuscles": "pectorals",
          "secondaryMuscles": "shoulders,Triceps",
          "mediaUrl": "https://static.exercisedb.dev/media/EIeI8Vf.gif",
          "description": "Lie flat on a bench with your feet flat on the ground. $$ Grip the barbell slightly wider than shoulder-width apart. $$ Lower bar to chest with control. $$ Press bar back up to starting position."
        }
      ]
    }
  ]
}
```

**Key Features:**

*   **workoutGroups**: Array of workout days/groups
*   **selectedExercises**: Array of exercises for each group
*   **description**: Exercise instructions separated by `$$` for easy parsing
*   **Complete metadata**: Body part, equipment, target/secondary muscles, media URL

**Implementation Details:**

*   Pydantic models in [`fastapiserver/models/workout_plan.py`](fastapiserver/models/workout_plan.py)
*   RAG pipeline post-processing in [`fastapiserver/services/rag_pipeline.py`](fastapiserver/services/rag_pipeline.py)
*   Automatic warmup/cooldown generation with custom format
*   Frontend JavaScript handles both old and new formats for backward compatibility

## � Changelog

### Version 2.2.0 (2026-06-16) - Custom Format & Auto-Cleanup

#### 🎯 API Response Format Changes

*   **Custom Format**: Complete overhaul to match Android app requirements
    *   Changed `workout_days` → `workoutGroups`
    *   Changed `exercises` → `selectedExercises`
    *   Added `isAiGenerated` flag to workout groups
    *   Exercise fields: `exerciseDbId`, `exerciseName`, `bodyPart`, `equipments`, `targetMuscles`, `secondaryMuscles`, `mediaUrl`, `description`
    *   Instructions formatted with `$$` separator for easy parsing

#### 🧹 Memory Management

*   **Automatic Model Cleanup**: Models are automatically unloaded after each workout generation
*   **Resource Optimization**: Prevents memory leaks and reduces RAM usage
*   **Service Factory**: Caching disabled for workout generation to enable cleanup

#### 🔧 Code Improvements

*   Updated Pydantic models to match custom format
*   Enhanced RAG pipeline post-processing for format conversion
*   Updated warmup/cooldown services to generate custom format
*   Frontend JavaScript updated to handle both old and new formats
*   Improved error handling and validation

#### 📁 Files Modified

*   `fastapiserver/models/workout_plan.py` - New custom format models
*   `fastapiserver/services/rag_pipeline.py` - Format conversion in post\_process\_response
*   `fastapiserver/services/warmup_cooldown.py` - Custom format generation
*   `fastapiserver/main.py` - Automatic model cleanup after generation
*   `flask/static/js/app.js` - Backward-compatible format handling

### Version 2.1.0 (2026-05-31) - Enterprise-Grade Improvements

#### 🔒 Security Enhancements

*   **CORS Configuration**: Environment-based CORS with `ALLOWED_ORIGINS` variable
*   **Rate Limiting**: 5 requests/minute per IP on workout generation endpoint
*   **Input Validation**: Comprehensive client and server-side validation

#### 🏗️ Architecture Improvements

*   **Dynamic Model Selection**: Switch between LLM providers without server restart
*   **Service Factory Pattern**: Efficient service creation and caching
*   **Thread-Safe Initialization**: Vector store with proper locking mechanisms
*   **Memory Management**: Automatic MLX model cleanup and garbage collection

#### ⚡ Performance Optimizations

*   **Service Caching**: Reuse services across requests for better performance
*   **Response Compression**: GZip middleware for reduced bandwidth
*   **Retry Logic**: Exponential backoff for transient API failures
*   **Efficient Exercise Loading**: Skip vector DB rebuild when data exists

#### 🎯 New Features

*   **Model Listing API**: `/api/v1/models` endpoint for available models
*   **Warm-up/Cool-down Generation**: Automatic exercise suggestions
*   **OMLX Integration**: Full support for OMLX server with API key authentication
*   **Structured Logging**: Request IDs and JSON logging support
*   **Health Monitoring**: Enhanced health check with service status

#### 🔧 Configuration

*   **Environment-Based URLs**: `FASTAPI_URL`, `FRONTEND_URL` configuration
*   **Flexible LLM Setup**: Support for MLX, GGUF, OMLX, LM Studio, OpenAI, Anthropic, Groq
*   **Port Configuration**: FastAPI on 7501, Flask on 7500 (avoiding OMLX port 8000)

#### 📁 Code Organization

*   **Directory Rename**: `app/` → `fastapiserver/`, `frontend/` → `flask/`
*   **Modular Services**: Clear separation of concerns
*   **Middleware Layer**: Request ID tracking and logging
*   **Utility Functions**: Shared JSON parsing and validation

#### 🐛 Bug Fixes

*   Fixed OMLX API key authentication (proper handling of None keys)
*   Fixed import optimization and circular dependencies
*   Fixed port conflicts with OMLX server
*   Fixed model configuration validation

#### 📚 Documentation

*   Updated README with dynamic model selection guide
*   Added comprehensive `.env.example` with all options
*   Improved API documentation references
*   Added troubleshooting section

### Version 2.0.0 (2026-05-30) - Major Refactor

*   Initial production-ready release
*   RAG pipeline implementation
*   Multi-LLM support
*   Vector database integration

### Version 1.0.0 (2026-05-29) - Initial Release

*   Basic workout generation
*   ExerciseDB integration
*   Simple LLM interface

---

## 🙏 Acknowledgments

*   **ExerciseDB**: Exercise data API
*   **ChromaDB**: Vector database
*   **MLX**: Apple Silicon ML framework
*   **OpenAI**: API and models
*   **Anthropic**: Claude models
*   **Groq**: Fast inference
*   **OMLX**: OpenAI-compatible MLX server

---

**Version**: 2.3.0  
**Last Updated**: 2026-06-24  
**Status**: Production Ready ✅

```
docker run -p 8080:8080 semitechnologies/weaviate
```

```
docker run -p 6333:6333 qdrant/qdrant
```

```
pip install faiss-cpu
```

```
pip uninstall llama-cpp-python
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

```
pip install faiss-cpu
```

```
pip install --only-binary :all: chromadb
```

```
# After installation, check where packages are
venv\Scripts\pip list

# Should show packages installed in venv\Lib\site-packages
```

```
# Create venv
python -m venv venv

# Activate venv (IMPORTANT!)
venv\Scripts\activate.bat

# Verify you're in venv (should show venv path)
where python

# Now install
pip install -r requirements.txt
```

```
run_frontend.bat
```

```
docker-compose --profile with-ollama up -d
docker exec -it ollama ollama pull llama3.2
```

```
# Windows
netstat -ano | findstr :7500

# Mac/Linux
lsof -i :7500

# Solution: Change port in docker-compose.yml
ports:
  - "8500:7500"  # Use 8500 instead
```

```
# Test if server is responding
curl http://127.0.0.1:1234/v1/models
```

```
# In .env file
LLM_BASE_URL=http://127.0.0.1:1234/v1
LLM_MODEL=local-model
```

```
bash run_frontend.sh
```

```
git clone <repository-url>
cd gym-workout-rag-backend
```