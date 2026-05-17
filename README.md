# Gym Workout RAG Backend

AI-powered personalized workout planner using Retrieval-Augmented Generation (RAG) with ChromaDB vector database and multiple LLM deployment options.

## 🌟 Features

- **RAG Pipeline**: Retrieves relevant exercises from 1500+ exercises using semantic search
- **Multiple LLM Options**: MLX, OMLX, GGUF, LM Studio, OpenAI, Anthropic, Groq
- **Vector Database**: ChromaDB with sentence-transformers embeddings
- **Modern Frontend**: Beautiful, responsive UI with gradient design
- **Scalable Architecture**: Blueprint-based Flask app with modular design
- **Persistent Storage**: Vector database persists between restarts

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- macOS (for MLX models) or any OS (for other options)
- 8GB+ RAM recommended

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd gym-workout-rag-backend
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

5. **Run the application**:
```bash
cd frontend
python app.py
```

The application will:
- Start FastAPI backend on port 8000
- Fetch exercises from ExerciseDB (first run only)
- Create embeddings and load into ChromaDB
- Start Flask frontend on port 5000

Access the UI at: **http://localhost:5000**

## 📁 Project Structure

```
gym-workout-rag-backend/
├── app/                          # FastAPI Backend
│   ├── main.py                  # FastAPI application
│   ├── config.py                # Configuration
│   ├── models/                  # Pydantic models
│   ├── services/                # Business logic
│   │   ├── exercisedb_client.py # Exercise API client
│   │   ├── vector_store.py      # ChromaDB interface
│   │   ├── llm_service.py       # LLM integration
│   │   ├── gguf_service.py      # GGUF model support
│   │   ├── mlx_agent_service.py # MLX agent with tools
│   │   └── rag_pipeline.py      # RAG orchestration
│   └── utils/                   # Utilities
│
├── frontend/                     # Flask Frontend
│   ├── app.py                   # Application factory
│   ├── api/                     # API Blueprint
│   │   └── routes.py           # API endpoints
│   ├── utils/                   # Utilities
│   │   └── server_manager.py   # Backend lifecycle
│   ├── static/                  # Static assets
│   │   ├── css/styles.css      # Modern CSS
│   │   └── js/app.js           # ES6+ JavaScript
│   └── templates/               # Jinja2 templates
│       └── index.html          # Main SPA
│
├── docs/                        # Documentation
│   ├── OMLX_SETUP.md           # OMLX setup guide
│   └── FRONTEND_ARCHITECTURE.md # Frontend docs
│
├── data/                        # Data storage
│   └── chroma_db/              # Vector database
│
├── .env.example                 # Environment template
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🎯 LLM Deployment Options

### 1. MLX Local Models (Default) 🍎
**Best for**: Mac users, agent mode with tool calling

```bash
# .env configuration
USE_MLX=true
MLX_MODEL_PATH=/path/to/mlx-community/Qwen3.5-4B-MLX-4bit
```

**Pros**: Free, private, agent capabilities  
**Cons**: Mac only, slower than cloud APIs

### 2. OMLX Server 🚀
**Best for**: Mac users wanting OpenAI-compatible API

```bash
# Install and run
pip install omlx
omlx serve --model mlx-community/Qwen3.5-4B-MLX-4bit --port 8000

# .env configuration
USE_MLX=false
LLM_BASE_URL=http://127.0.0.1:8000/v1
```

See [`docs/OMLX_SETUP.md`](docs/OMLX_SETUP.md) for details.

### 3. GGUF Models 💻
**Best for**: Cross-platform compatibility

```bash
# .env configuration
USE_GGUF=true
GGUF_MODEL_PATH=/path/to/model.gguf
GGUF_N_CTX=4096
GGUF_N_GPU_LAYERS=0
```

### 4. Local Servers (LM Studio/OLLAMA) 🖥️
**Best for**: Easy local deployment

```bash
# .env configuration
USE_MLX=false
LLM_BASE_URL=http://127.0.0.1:1234/v1
```

### 5. Public APIs (OpenAI/Anthropic/Groq) ☁️
**Best for**: Best quality, fastest inference

```bash
# .env configuration
USE_MLX=false
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-...
```

## 🎨 Frontend Features

- **Modern UI**: Beautiful gradient design with smooth animations
- **Responsive**: Works on desktop, tablet, and mobile
- **Two-step Workflow**: Model selection → Workout form
- **Real-time Validation**: Client and server-side validation
- **Error Handling**: Clear error messages and recovery
- **Loading States**: Progress indicators during generation

See [`frontend/README.md`](frontend/README.md) for details.

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
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

- `POST /api/v1/generate` - Generate workout plan
- `GET /health` - Health check with vector DB status

### Flask Frontend (Port 5000)

- `GET /` - Main application page
- `POST /api/generate` - Proxy to backend
- `GET /api/health` - Combined health check

## 🧪 Development

### Running Backend Only

```bash
python -m uvicorn app.main:app --reload
```

### Running Frontend Only

```bash
cd frontend
python app.py
```

### Project Dependencies

- **FastAPI**: Backend API framework
- **Flask**: Frontend web framework
- **ChromaDB**: Vector database
- **sentence-transformers**: Embeddings
- **mlx-lm**: MLX model support (Mac only)
- **llama-cpp-python**: GGUF model support
- **openai**: OpenAI API client
- **httpx**: HTTP client

## 📝 Usage Example

1. **Start the application**:
```bash
cd frontend
python app.py
```

2. **Open browser**: http://localhost:5000

3. **Select AI model** (Step 1):
   - Choose your preferred model type
   - Configure model settings (informational)

4. **Fill profile** (Step 2):
   - Height, weight, age, gender
   - Fitness level, goals
   - Available equipment
   - Days per week, session duration

5. **Generate workout**:
   - Click "Generate Workout Plan"
   - Wait 30-60 seconds
   - View personalized workout plan

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is available
lsof -i :8000
kill -9 <PID>
```

### Frontend connection error
```bash
# Verify backend is running
curl http://localhost:8000/health
```

### Slow generation
- Use smaller model (e.g., 4B instead of 9B)
- Try LM Studio or public APIs
- Increase timeout in frontend

### Vector DB issues
```bash
# Clear and rebuild
rm -rf data/chroma_db/
# Restart application (will refetch exercises)
```

## 📚 Documentation

- [`frontend/README.md`](frontend/README.md) - Frontend documentation
- [`docs/FRONTEND_ARCHITECTURE.md`](docs/FRONTEND_ARCHITECTURE.md) - Architecture details
- [`docs/OMLX_SETUP.md`](docs/OMLX_SETUP.md) - OMLX setup guide
- [`.env.example`](.env.example) - Configuration reference

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **ExerciseDB**: Exercise data API
- **ChromaDB**: Vector database
- **MLX**: Apple Silicon ML framework
- **OpenAI**: API and models
- **Anthropic**: Claude models
- **Groq**: Fast inference

---

**Version**: 2.0.0  
**Last Updated**: 2026-05-17  
**Status**: Production Ready ✅