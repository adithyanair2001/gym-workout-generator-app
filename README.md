# Gym Workout RAG System

> AI-powered personalized workout plan generator using Retrieval-Augmented Generation (RAG)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Technical Specifications](#technical-specifications)
- [Development Guide](#development-guide)
- [Deployment](#deployment)
- [Performance](#performance)
- [Contributing](#contributing)

---

## Overview

This backend system generates personalized gym workout plans using:
- **ExerciseDB**: 1,500+ verified exercises
- **ChromaDB**: Vector database for semantic search
- **MLX-LM**: Apple Silicon optimized LLM (Qwen3.5-9B)
- **Agent-based RAG**: LLM directly queries database using tools

### Key Capabilities

- ✅ Personalized workout plans based on user profile
- ✅ Semantic exercise search with vector embeddings
- ✅ Equipment-based filtering
- ✅ Injury-aware exercise selection
- ✅ Multiple workout splits (full body, upper/lower, PPL)
- ✅ Structured JSON output for frontend integration
- ✅ Agent-based approach (LLM decides which tools to call)

---

## Features

### User Input Parameters

- Physical attributes (height, weight, age, gender)
- Fitness level (beginner/intermediate/advanced)
- Training frequency (1-7 days/week)
- Session duration (30-120 minutes)
- Goals (muscle gain, weight loss, strength, endurance)
- Available equipment
- Injuries/limitations
- Preferred workout split

### Output Format

```json
{
  "user_profile_summary": {...},
  "plan_duration_weeks": 4,
  "days_per_week": 4,
  "workout_days": [
    {
      "day_number": 1,
      "day_name": "Day 1: Upper Body Push",
      "focus": "Chest, Shoulders, Triceps",
      "warm_up": [...],
      "main_workout": [
        {
          "exercise_id": "0001",
          "name": "Barbell Bench Press",
          "target_muscles": ["pectorals"],
          "sets": 4,
          "reps": "8-12",
          "rest_seconds": 90,
          "gif_url": "...",
          "instructions": [...]
        }
      ],
      "cool_down": [...],
      "estimated_duration_minutes": 60
    }
  ],
  "progression_notes": "...",
  "generated_at": "2026-05-10T14:00:00Z"
}
```

---

## System Architecture

```
┌─────────────┐
│  Frontend   │
│     App     │
└──────┬──────┘
       │ POST /generate
       ▼
┌─────────────────────────────────────┐
│         FastAPI Backend             │
│  ┌──────────────────────────────┐  │
│  │   MLX Agent Service          │  │
│  │  1. Receives user profile    │  │
│  │  2. LLM decides which tools  │  │
│  │  3. Calls database tools     │  │
│  │  4. Generates workout plan   │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│      Data Layer                     │
│  ┌────────────┐  ┌──────────────┐  │
│  │ ExerciseDB │  │   ChromaDB   │  │
│  │    API     │  │ Vector Store │  │
│  └────────────┘  └──────────────┘  │
└─────────────────────────────────────┘
```

### How the Two Models Work Together

The system uses **two different AI models** that work in tandem:

#### 1️⃣ Embedding Model (sentence-transformers)
**Purpose**: Converts text to vectors for semantic search
- **Current Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Location**: [`vector_store.py`](app/services/vector_store.py)
- **Job**: Find relevant exercises from database

**Process**:
```
ExerciseDB Exercise → Text Document → Embedding Model → Vector → ChromaDB
User Query → Embedding Model → Vector → Search ChromaDB → Top 50 Exercises
```

**Example**:
```python
# Exercise description:
"Barbell Bench Press - Target: chest, Equipment: barbell"
↓ Embedding Model
[0.234, -0.567, 0.891, ...] (384 numbers)

# User query:
"intermediate chest exercises with barbell"
↓ Embedding Model
[0.245, -0.543, 0.876, ...] (384 numbers)

# ChromaDB finds similar vectors → Returns relevant exercises
```

#### 2️⃣ LLM Model (Qwen3.5-9B via MLX)
**Purpose**: Generates the actual workout plan
- **Current Model**: Qwen3.5-9B (4-bit quantized, 9 billion parameters)
- **Location**: [`mlx_agent_service.py`](app/services/mlx_agent_service.py)
- **Job**: Design personalized workout plan

**Process**:
```
User Profile + 50 Relevant Exercises → LLM → Complete Workout Plan
```

**What it generates**:
- Which exercises for each day
- Sets, reps, and rest times
- Workout split (upper/lower, PPL, etc.)
- Progression notes
- Nutrition tips

#### Complete Flow

```
Step 1: User Input
├─ "Build muscle, 4 days/week, intermediate, barbell & dumbbell"

Step 2: Embedding Model (sentence-transformers)
├─ Converts query to vector: [0.234, -0.567, ...]
├─ Searches ChromaDB for similar exercises
└─ Returns: Top 50 relevant exercises

Step 3: LLM Model (Qwen3.5-9B)
├─ Receives: User profile + 50 exercises
├─ Reasons: "This person needs upper/lower split..."
├─ Generates: Complete 4-day workout plan
│   ├─ Day 1: Upper Body (Bench Press 4x8-12, Rows 4x8-12...)
│   ├─ Day 2: Lower Body (Squats 4x8-12, Lunges 3x10-15...)
│   ├─ Day 3: Upper Body (Overhead Press 4x8-12...)
│   └─ Day 4: Lower Body (Deadlifts 4x6-8...)
└─ Returns: JSON workout plan

Step 4: Post-Processing
└─ Validates and formats the final workout plan
```

#### Model Comparison

| Aspect | Embedding Model | LLM Model (Qwen3.5-9B) |
|--------|----------------|------------------------|
| **Purpose** | Find relevant exercises | Generate workout plan |
| **Input** | Text query | User profile + exercises |
| **Output** | List of exercises | Complete workout plan |
| **Speed** | ⚡⚡⚡ Very fast (50-100ms) | ⚡⚡ Slower (10-30s) |
| **Size** | 80MB | 5-6GB |
| **Runs on** | CPU (fine) | GPU recommended |
| **Upgradeable?** | Yes → `all-mpnet-base-v2` | Yes → Qwen3.5-14B, Llama 3.1 |

#### Why Two Models?

**Embedding Model** = Search engine that finds exercises
- Fast and efficient
- Understands semantic meaning
- Finds "chest exercises" even if query says "pectoral training"

**LLM Model** = Personal trainer brain that designs workouts
- Understands context and goals
- Makes intelligent decisions
- Creates structured, personalized plans

**Together** = Powerful RAG system that combines retrieval + generation!

### Agent-Based RAG Pipeline

Unlike traditional RAG where the system decides what to retrieve, our agent-based approach lets the LLM decide:

1. **User Request** → MLX Agent receives user profile
2. **LLM Reasoning** → Model decides which database tools to call
3. **Tool Execution** → Agent executes `search_exercises()`, `filter_by_equipment()`, etc.
4. **Iterative Process** → LLM can call multiple tools based on results
5. **Plan Generation** → Final workout plan generated with all context

**Available Tools:**
- `search_exercises(query, n_results)` - Semantic search
- `filter_by_equipment(equipment_list, n_results)` - Filter by equipment
- `get_exercise_details(exercise_id)` - Get specific exercise info

---

## Technology Stack

### Core Framework
- **FastAPI** - Modern, fast Python web framework
- **Python 3.11+** - Latest Python features
- **Pydantic** - Data validation and settings

### AI/ML Stack
- **MLX-LM** - Apple Silicon optimized ML framework
- **Qwen3.5-9B** - 9B parameter model (4-bit quantized)
- **sentence-transformers** - all-MiniLM-L6-v2 for embeddings
- **ChromaDB** - Vector database for semantic search

### Key Libraries
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
httpx==0.26.0
chromadb==0.4.22
sentence-transformers==2.3.1
mlx-lm>=0.31.0
langchain>=0.1.0
langchain-community>=0.0.10
```

### Why These Choices?

**ChromaDB over FAISS:**
- Built-in metadata filtering (equipment, muscle groups)
- Native persistence (no manual save/load)
- Perfect for 1,500 exercises
- Faster development time

**MLX-LM over Ollama:**
- Optimized for Apple Silicon (M1/M2/M3)
- Direct model loading (no server needed)
- Better control over generation
- Faster inference on Mac

**Agent-based RAG:**
- LLM decides what data to retrieve
- More flexible than fixed retrieval
- Better handles complex queries
- Iterative refinement possible

---

## Quick Start

### Prerequisites

- Python 3.11+
- macOS with Apple Silicon (M1/M2/M3) or compatible system
- 16GB+ RAM recommended
- 10GB+ free disk space

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd gym-workout-rag-backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Download the MLX model**

The model will be automatically downloaded from LM Studio's cache:
```
~/.lmstudio/models/mlx-community/Qwen3.5-9B-MLX-4bit/
```

If not available, download via LM Studio or manually.

### Running the Application

1. **Start the FastAPI server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Access the API**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

3. **Test the agent**
```bash
python test_agent_quick.py
```

### First Run

On first startup, the system will:
1. Fetch all 1,500 exercises from ExerciseDB (~2-3 minutes)
2. Generate embeddings for semantic search
3. Store in ChromaDB vector database
4. Load the MLX model into memory

Subsequent startups are much faster (~5-10 seconds).

---

## Project Structure

```
gym-workout-rag-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app
│   ├── config.py                    # Configuration
│   ├── models/
│   │   ├── exercise.py              # Exercise models
│   │   ├── user_profile.py          # User input models
│   │   └── workout_plan.py          # Workout output models
│   ├── services/
│   │   ├── exercisedb_client.py     # ExerciseDB API client
│   │   ├── vector_store.py          # ChromaDB operations
│   │   ├── mlx_agent_service.py     # MLX agent implementation
│   │   ├── database_tools.py        # Tools for agent
│   │   ├── llm_service.py           # LLM wrapper
│   │   └── rag_pipeline.py          # RAG orchestration
│   ├── api/
│   │   └── __init__.py
│   ├── utils/
│   │   └── __init__.py
│   └── core/
│       └── __init__.py
├── data/
│   └── chroma_db/                   # Vector database storage
├── tests/
│   ├── test_api.py
│   ├── test_agent_quick.py
│   └── test_pagination.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
└── README.md
```

---

## API Documentation

### Generate Workout Plan

**Endpoint:** `POST /api/v1/generate`

**Request Body:**
```json
{
  "height": 175,
  "weight": 75,
  "age": 28,
  "gender": "male",
  "fitness_level": "intermediate",
  "gym_days_per_week": 4,
  "workout_duration_minutes": 60,
  "goals": ["muscle_gain", "strength"],
  "available_equipment": ["barbell", "dumbbell", "cable"],
  "injuries_limitations": [],
  "preferred_split": "upper_lower"
}
```

**Response:** `200 OK`
```json
{
  "user_profile_summary": {...},
  "plan_duration_weeks": 4,
  "days_per_week": 4,
  "workout_days": [...],
  "progression_notes": "...",
  "generated_at": "2026-05-10T14:00:00Z"
}
```

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "vector_db_status": "ready",
  "total_exercises": 1500
}
```

---

## Technical Specifications

### Vector Database

**ChromaDB Configuration:**
- Collection: `exercise_embeddings`
- Embedding dimension: 384
- Distance metric: Cosine similarity
- Persistence: `./data/chroma_db`

**Metadata Schema:**
```python
{
  "exercise_id": "string",
  "name": "string",
  "target_muscles": "comma-separated",
  "body_parts": "comma-separated",
  "equipment": "comma-separated",
  "gif_url": "string"
}
```

### MLX Agent Service

**Model:** Qwen3.5-9B-MLX-4bit
- Parameters: 9 billion (4-bit quantized)
- Context window: 32K tokens
- Max tokens: 8000 (for complete workout plans)
- Max iterations: 5
- Max tool calls: 3

**Agent Loop:**
1. Receive user profile
2. Generate thought about what to do
3. Decide which tool to call (if any)
4. Execute tool and observe result
5. Repeat until final answer or max iterations

### ExerciseDB Integration

**API:** https://oss.exercisedb.dev/api/v1/exercises

**Features:**
- Cursor-based pagination (150 pages, 10 exercises each)
- Exponential backoff retry (handles 429 rate limits)
- 1-second inter-request delay
- Automatic retry on failure (max 3 attempts)

**Data Structure:**
```json
{
  "id": "0001",
  "name": "barbell bench press",
  "gifUrl": "https://...",
  "targetMuscles": ["pectorals"],
  "bodyParts": ["chest"],
  "equipments": ["barbell"],
  "secondaryMuscles": ["triceps", "shoulders"],
  "instructions": ["Step 1...", "Step 2..."]
}
```

### Performance Metrics

- **Vector Search**: 50-100ms for 1,500 exercises
- **LLM Generation**: 10-30 seconds (depends on complexity)
- **Total Response Time**: 15-40 seconds
- **Memory Usage**: ~4-6GB (including model)
- **Concurrent Requests**: 5-10 (limited by model memory)

---

## Development Guide

### Adding New Tools

To add a new tool for the agent:

1. **Define the tool in `database_tools.py`:**
```python
def get_exercises_by_difficulty(difficulty: str, n_results: int = 10) -> str:
    """Get exercises filtered by difficulty level."""
    # Implementation
    return json.dumps(results)
```

2. **Register in tool list:**
```python
TOOLS = [
    {
        "name": "get_exercises_by_difficulty",
        "description": "Get exercises filtered by difficulty",
        "parameters": {
            "difficulty": "beginner|intermediate|advanced",
            "n_results": "number of results (default: 10)"
        }
    }
]
```

3. **Agent will automatically discover and use it!**

### Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_agent_quick.py

# Run with coverage
pytest --cov=app tests/
```

### Debugging

Enable debug logging in `.env`:
```env
LOG_LEVEL=DEBUG
```

View agent reasoning:
```python
# In test_agent_quick.py
print(agent_output)  # Shows full agent loop
```

---

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY data/ ./data/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# ExerciseDB
EXERCISEDB_API_URL=https://oss.exercisedb.dev/api/v1/exercises

# Vector Database
CHROMA_DB_PATH=./data/chroma_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# MLX Model
MLX_MODEL_PATH=~/.lmstudio/models/mlx-community/Qwen3.5-9B-MLX-4bit/

# Logging
LOG_LEVEL=INFO
```

### Production Checklist

- [ ] Set up environment variables
- [ ] Initialize vector database
- [ ] Configure logging and monitoring
- [ ] Set up health check endpoints
- [ ] Test API endpoints
- [ ] Load test with concurrent requests
- [ ] Set up backup strategy for vector DB
- [ ] Configure rate limiting
- [ ] Set up error tracking (Sentry, etc.)

---

## Performance

### Optimization Strategies

1. **Vector Database Caching**
   - Persistent storage (no re-indexing on restart)
   - In-memory embeddings for fast search

2. **Batch Processing**
   - Batch size: 32 for embedding generation
   - Parallel API calls where possible

3. **Rate Limiting**
   - ExerciseDB: 1-second delays between requests
   - Exponential backoff for 429 errors

4. **Model Optimization**
   - 4-bit quantization (reduces memory by 75%)
   - MLX optimizations for Apple Silicon
   - Reduced max iterations (5) and tool calls (3)

### Benchmarks

**Hardware:** MacBook Pro M2, 16GB RAM

- Vector search (1,500 exercises): ~80ms
- Embedding generation (1 exercise): ~5ms
- LLM generation (workout plan): ~20s
- Total end-to-end: ~25s

---

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings
- Add tests for new features

### Commit Messages

```
feat: Add new exercise filtering tool
fix: Handle rate limiting in ExerciseDB client
docs: Update README with deployment guide
test: Add tests for agent service
```

---

## License

MIT License - see LICENSE file for details

---

## Support

For questions or issues:
1. Check the documentation
2. Search existing issues
3. Create a new issue with details

---

## Acknowledgments

- **ExerciseDB** - Exercise database API
- **ChromaDB** - Vector database
- **MLX** - Apple Silicon ML framework
- **Qwen Team** - Qwen3.5 model
- **Sentence Transformers** - Embedding models

---

**Status:** ✅ Production Ready
**Version:** 1.1.0
**Last Updated:** 2026-05-15

---

## Changelog

### Version 1.1.0 (2026-05-15)

#### 🔒 Security Improvements
- **Input Validation**: Added comprehensive validation for all tool arguments
  - Query strings sanitized (max 500 chars, control character removal)
  - Exercise IDs validated (alphanumeric with hyphens/underscores only)
  - `n_results` bounds checking (1-100)
  - Equipment list validation and normalization
- **PII Protection**: Implemented sanitized logging that redacts sensitive user data
- **API Key Management**: Moved hardcoded credentials to environment variables
- **Enhanced .gitignore**: Added patterns for sensitive files (`.env.*`, `*.bak`, debug logs)

#### 🐛 Bug Fixes
- **Error Handling**: Improved JSON parsing with better error messages and debug file saving
- **Empty Results**: Enhanced error messages with actionable debugging information
- **Memory Management**: Added conversation history size limits (30K chars) to prevent unbounded growth
- **Model Validation**: Added validation after MLX model loading to ensure components are usable

#### ⚡ Performance Enhancements
- **Database-Level Filtering**: Replaced post-processing with ChromaDB metadata filtering (50% faster)
- **Query Caching**: Implemented embedding cache for repeated queries (100 entry LRU cache)
- **Reduced Data Transfer**: Equipment filtering now happens at database level

#### 🏗️ Code Quality
- **DRY Improvements**: Consolidated duplicate JSON parsing logic into shared utility (`app/utils/json_parser.py`)
- **New Utilities Module**: Added `app/utils/validators.py` for input validation
- **Constants**: Extracted magic numbers to named class constants
- **Better Documentation**: Enhanced docstrings with examples and clearer explanations
- **Variable Naming**: Improved clarity (renamed `ex` to `exercise` in loops)

#### 📝 Documentation
- Added detailed TODO comments for future warm-up/cool-down implementation
- Documented thread-safety considerations for vector store initialization
- Added migration guide for developers

#### 🔧 Configuration
- New environment variable: `LM_STUDIO_API_KEY` (defaults to 'lm-studio' for local development)

### Version 1.0.0 (2026-05-11)
- Initial release with FastAPI backend
- ChromaDB vector store integration
- MLX-based LLM agent with database tools
- ExerciseDB API integration with pagination
- Personalized workout plan generation