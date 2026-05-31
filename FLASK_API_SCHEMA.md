# Flask Server API Schema

This document describes all API endpoints available in the Flask frontend server.

## Base URL

```
Flask Frontend: http://localhost:7500
FastAPI Backend: http://localhost:7501
```

**Note:** FastAPI uses port 7501 to avoid conflicts with OMLX server (which uses port 8000).

## Authentication

No authentication required for local development. All endpoints are publicly accessible.

---

## Endpoints

### 1. Health Check

Check the health status of both Flask frontend and FastAPI backend services.

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "frontend": "healthy",
  "backend": {
    "status": "healthy",
    "timestamp": "2026-05-31T16:00:00Z"
  }
}
```

**Error Response (503):**
```json
{
  "frontend": "healthy",
  "backend": {
    "status": "unhealthy",
    "error": "Connection refused"
  }
}
```

---

### 2. Validate Model Configuration

Validate LLM model configuration and test connection before generating workouts.

**Endpoint:** `POST /api/validate-model`

**Request Body:**
```json
{
  "model_type": "mlx|omlx|gguf|local_server|openai|anthropic|groq",
  "llm_base_url": "http://localhost:8000",  // Optional, for server-based models
  "llm_model": "model-name",                 // Optional, model identifier
  "llm_api_key": "sk-...",                   // Optional, for API-based models
  "mlx_model_path": "/path/to/model",        // Optional, for MLX models
  "gguf_model_path": "/path/to/model.gguf"   // Optional, for GGUF models
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Model found and accessible",
  "details": {
    "path": "/path/to/model",
    "exists": true,
    "type": "mlx"
  }
}
```

**Error Response (400/404/503):**
```json
{
  "success": false,
  "message": "Error description"
}
```

**Supported Model Types:**

1. **MLX** - Apple Silicon optimized models
   - Requires: `mlx_model_path`
   - Validates: Directory exists and is accessible

2. **OMLX** - OMLX server (OpenAI-compatible)
   - Requires: `llm_base_url`
   - Optional: `llm_model`
   - Tests: Connection to `/models` endpoint

3. **GGUF** - Quantized models
   - Requires: `gguf_model_path`
   - Validates: File exists and has `.gguf` extension

4. **Local Server** - LM Studio/OLLAMA
   - Requires: `llm_base_url`
   - Tests: Connection to `/models` endpoint

5. **OpenAI** - OpenAI API
   - Requires: `llm_api_key`, `llm_model`
   - Tests: API key validity

6. **Anthropic** - Claude API
   - Requires: `llm_api_key`, `llm_model`
   - Tests: API key validity

7. **Groq** - Groq API
   - Requires: `llm_api_key`, `llm_model`
   - Tests: API key validity

---

### 3. List Available Models

List available models from the configured LLM provider.

**Endpoint:** `GET /api/models`

**Response (200):**
```json
{
  "success": true,
  "provider": "openai",
  "models": [
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "description": "Most capable model"
    }
  ]
}
```

**Error Response (503/504):**
```json
{
  "success": false,
  "message": "Cannot connect to backend server"
}
```

---

### 4. Generate Workout Plan

Generate a personalized workout plan based on user profile.

**Endpoint:** `POST /api/generate`

**Request Body:**
```json
{
  "model_config": {
    "model_type": "openai",
    "llm_model": "gpt-4"
  },
  "height": 175.5,
  "weight": 75.0,
  "age": 30,
  "gender": "male",
  "fitness_level": "intermediate",
  "days_per_week": 4,
  "session_duration": 60,
  "goals": ["muscle_gain", "strength"],
  "equipment": ["barbell", "dumbbells", "bench"],
  "injuries": "lower_back_pain",
  "preferred_split": "upper_lower"
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `height` | float | Yes | Height in cm |
| `weight` | float | Yes | Weight in kg |
| `age` | integer | Yes | Age in years (18-100) |
| `gender` | string | Yes | "male" or "female" |
| `fitness_level` | string | Yes | "beginner", "intermediate", or "advanced" |
| `days_per_week` | integer | Yes | Training days per week (1-7) |
| `session_duration` | integer | Yes | Session duration in minutes (15-180) |
| `goals` | array/string | Yes | Fitness goals (comma-separated or array) |
| `equipment` | array/string | Yes | Available equipment (comma-separated or array) |
| `injuries` | string | No | Injuries or limitations |
| `preferred_split` | string | Yes | "full_body", "upper_lower", "push_pull_legs", or "bro_split" |

**Response (200):**
```json
{
  "success": true,
  "workout_plan": {
    "user_profile": {
      "height": 175.5,
      "weight": 75.0,
      "age": 30,
      "gender": "male",
      "fitness_level": "intermediate",
      "gym_days_per_week": 4,
      "workout_duration_minutes": 60,
      "goals": ["muscle_gain", "strength"],
      "available_equipment": ["barbell", "dumbbells", "bench"],
      "injuries_limitations": ["lower_back_pain"],
      "preferred_split": "upper_lower"
    },
    "weekly_schedule": [
      {
        "day": "Monday",
        "focus": "Upper Body",
        "exercises": [
          {
            "name": "Bench Press",
            "sets": 4,
            "reps": "8-10",
            "rest": "90s",
            "notes": "Focus on controlled movement"
          }
        ]
      }
    ],
    "warm_up": {
      "duration_minutes": 10,
      "exercises": [
        {
          "name": "Arm Circles",
          "duration": "30s",
          "notes": "Both directions"
        }
      ]
    },
    "cool_down": {
      "duration_minutes": 10,
      "exercises": [
        {
          "name": "Chest Stretch",
          "duration": "30s",
          "notes": "Hold stretch"
        }
      ]
    },
    "nutrition_tips": [
      "Consume 1.6-2.2g protein per kg bodyweight",
      "Stay hydrated throughout the day"
    ],
    "progress_tracking": [
      "Track weight lifted each session",
      "Take progress photos monthly"
    ]
  }
}
```

**Error Responses:**

- **400 Bad Request:** Invalid input data
```json
{
  "success": false,
  "message": "Validation error: Age must be between 18 and 100"
}
```

- **503 Service Unavailable:** Backend server not running
```json
{
  "success": false,
  "message": "Cannot connect to backend server. Please ensure the FastAPI server is running."
}
```

- **504 Gateway Timeout:** Request took too long (>10 minutes)
```json
{
  "success": false,
  "message": "Request timeout after 10 minutes. The model may be too slow."
}
```

---

## ExerciseDB API Proxy Endpoints

The Flask server provides proxy endpoints to access the ExerciseDB API. These endpoints forward requests to the ExerciseDB API and return the results.

### 5. List All Exercises

Get a paginated list of all exercises from ExerciseDB.

**Endpoint:** `GET /api/exercises`

**Query Parameters:**
- `limit` (integer, optional): Number of exercises per page (1-200, default: 20)
- `cursor` (string, optional): Pagination cursor from previous response

**Example Request:**
```
GET /api/exercises?limit=50
GET /api/exercises?limit=50&cursor=eyJpZCI6IjEwMDAifQ
```

**Response (200):**
```json
{
  "success": true,
  "meta": {
    "total": 1500,
    "hasNextPage": true,
    "nextCursor": "eyJpZCI6IjEwNTAifQ"
  },
  "data": [
    {
      "id": "0001",
      "name": "3/4 Sit-Up",
      "gifUrl": "https://v2.exercisedb.io/image/abc123",
      "instructions": [
        "Lie flat on your back with your knees bent and feet flat on the ground.",
        "Place your hands behind your head with your elbows pointing outwards.",
        "Engaging your abs, slowly lift your upper body off the ground, curling forward until your torso is at a 45-degree angle.",
        "Pause for a moment at the top, then slowly lower your upper body back down to the starting position.",
        "Repeat for the desired number of repetitions."
      ],
      "targetMuscles": ["abs"],
      "bodyParts": ["waist"],
      "equipments": ["body weight"],
      "secondaryMuscles": ["hip flexors", "lower back"]
    }
  ]
}
```

---

### 6. Get Exercise by ID

Get detailed information about a specific exercise.

**Endpoint:** `GET /api/exercises/:id`

**Path Parameters:**
- `id` (string, required): Exercise ID (e.g., "0001")

**Example Request:**
```
GET /api/exercises/0001
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "0001",
    "name": "3/4 Sit-Up",
    "gifUrl": "https://v2.exercisedb.io/image/abc123",
    "instructions": [
      "Lie flat on your back with your knees bent and feet flat on the ground.",
      "Place your hands behind your head with your elbows pointing outwards.",
      "Engaging your abs, slowly lift your upper body off the ground, curling forward until your torso is at a 45-degree angle.",
      "Pause for a moment at the top, then slowly lower your upper body back down to the starting position.",
      "Repeat for the desired number of repetitions."
    ],
    "targetMuscles": ["abs"],
    "bodyParts": ["waist"],
    "equipments": ["body weight"],
    "secondaryMuscles": ["hip flexors", "lower back"]
  }
}
```

**Error Response (404):**
```json
{
  "success": false,
  "message": "Exercise not found"
}
```

---

### 7. Search Exercises

Search for exercises using fuzzy matching on exercise names.

**Endpoint:** `GET /api/exercises/search`

**Query Parameters:**
- `query` (string, required): Search query (e.g., "bench press")
- `limit` (integer, optional): Number of results (1-200, default: 20)
- `cursor` (string, optional): Pagination cursor

**Example Request:**
```
GET /api/exercises/search?query=bench%20press&limit=10
```

**Response (200):**
```json
{
  "success": true,
  "meta": {
    "total": 15,
    "hasNextPage": false,
    "nextCursor": null
  },
  "data": [
    {
      "id": "0025",
      "name": "Barbell Bench Press",
      "gifUrl": "https://v2.exercisedb.io/image/xyz789",
      "targetMuscles": ["pectorals"],
      "bodyParts": ["chest"],
      "equipments": ["barbell"]
    }
  ]
}
```

---

### 8. Filter by Target Muscle

Get exercises that target a specific muscle group.

**Endpoint:** `GET /api/exercises/target/:muscle`

**Path Parameters:**
- `muscle` (string, required): Target muscle (e.g., "pectorals", "biceps", "quadriceps")

**Query Parameters:**
- `limit` (integer, optional): Number of results (1-200, default: 20)
- `cursor` (string, optional): Pagination cursor

**Example Request:**
```
GET /api/exercises/target/pectorals?limit=20
```

**Response (200):**
```json
{
  "success": true,
  "meta": {
    "total": 45,
    "hasNextPage": true,
    "nextCursor": "eyJpZCI6IjAyMCJ9"
  },
  "data": [
    {
      "id": "0025",
      "name": "Barbell Bench Press",
      "targetMuscles": ["pectorals"],
      "bodyParts": ["chest"],
      "equipments": ["barbell"]
    }
  ]
}
```

---

### 9. Filter by Body Part

Get exercises for a specific body part.

**Endpoint:** `GET /api/exercises/bodypart/:part`

**Path Parameters:**
- `part` (string, required): Body part (e.g., "chest", "back", "legs")

**Query Parameters:**
- `limit` (integer, optional): Number of results (1-200, default: 20)
- `cursor` (string, optional): Pagination cursor

**Example Request:**
```
GET /api/exercises/bodypart/chest?limit=20
```

---

### 10. Filter by Equipment

Get exercises that use specific equipment.

**Endpoint:** `GET /api/exercises/equipment/:equipment`

**Path Parameters:**
- `equipment` (string, required): Equipment type (e.g., "barbell", "dumbbell", "body weight")

**Query Parameters:**
- `limit` (integer, optional): Number of results (1-200, default: 20)
- `cursor` (string, optional): Pagination cursor

**Example Request:**
```
GET /api/exercises/equipment/barbell?limit=20
```

---

### 11. List Target Muscles

Get a list of all available target muscle groups.

**Endpoint:** `GET /api/exercises/targets`

**Response (200):**
```json
{
  "success": true,
  "data": [
    "abs",
    "adductors",
    "biceps",
    "calves",
    "cardiovascular system",
    "delts",
    "forearms",
    "glutes",
    "hamstrings",
    "lats",
    "levator scapulae",
    "pectorals",
    "quads",
    "serratus anterior",
    "spine",
    "traps",
    "triceps",
    "upper back"
  ]
}
```

---

### 12. List Body Parts

Get a list of all available body parts.

**Endpoint:** `GET /api/exercises/bodyparts`

**Response (200):**
```json
{
  "success": true,
  "data": [
    "back",
    "cardio",
    "chest",
    "lower arms",
    "lower legs",
    "neck",
    "shoulders",
    "upper arms",
    "upper legs",
    "waist"
  ]
}
```

---

### 13. List Equipment Types

Get a list of all available equipment types.

**Endpoint:** `GET /api/exercises/equipments`

**Response (200):**
```json
{
  "success": true,
  "data": [
    "assisted",
    "band",
    "barbell",
    "body weight",
    "bosu ball",
    "cable",
    "dumbbell",
    "elliptical machine",
    "ez barbell",
    "hammer",
    "kettlebell",
    "leverage machine",
    "medicine ball",
    "olympic barbell",
    "resistance band",
    "roller",
    "rope",
    "skierg machine",
    "sled machine",
    "smith machine",
    "stability ball",
    "stationary bike",
    "stepmill machine",
    "tire",
    "trap bar",
    "upper body ergometer",
    "weighted",
    "wheel roller"
  ]
}
```

---

## Error Handling

All endpoints follow a consistent error response format:

```json
{
  "success": false,
  "message": "Error description"
}
```

### Common HTTP Status Codes

- **200 OK:** Request successful
- **400 Bad Request:** Invalid input data or parameters
- **401 Unauthorized:** Invalid API key (for external APIs)
- **404 Not Found:** Resource not found
- **429 Too Many Requests:** Rate limit exceeded
- **500 Internal Server Error:** Server error
- **503 Service Unavailable:** Backend service unavailable
- **504 Gateway Timeout:** Request timeout

---

## Rate Limiting

The ExerciseDB API has rate limits. The Flask server implements:
- Automatic retry with exponential backoff for 429 errors
- Request delays between pagination requests
- Maximum 5 retry attempts per request

---

## CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:7500` (Flask frontend)
- `http://localhost:7501` (FastAPI backend)
- Additional origins can be configured via `CORS_ORIGINS` environment variable

---

## Environment Variables

Configure the Flask server using these environment variables:

```bash
# FastAPI Backend URL
FASTAPI_URL=http://localhost:7501

# ExerciseDB API Configuration
EXERCISEDB_API_URL=https://exercisedb.p.rapidapi.com/exercises
EXERCISEDB_API_KEY=your_api_key_here

# CORS Configuration
CORS_ORIGINS=http://localhost:7500,http://localhost:7501

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

---

## Usage Examples

### Generate Workout Plan

```bash
curl -X POST http://localhost:7500/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "height": 175,
    "weight": 75,
    "age": 30,
    "gender": "male",
    "fitness_level": "intermediate",
    "days_per_week": 4,
    "session_duration": 60,
    "goals": ["muscle_gain"],
    "equipment": ["barbell", "dumbbells"],
    "preferred_split": "upper_lower"
  }'
```

### Search Exercises

```bash
curl "http://localhost:7500/api/exercises/search?query=bench%20press&limit=10"
```

### Get Exercises by Muscle

```bash
curl "http://localhost:7500/api/exercises/target/pectorals?limit=20"
```

### Validate Model

```bash
curl -X POST http://localhost:7500/api/validate-model \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "openai",
    "llm_api_key": "sk-...",
    "llm_model": "gpt-4"
  }'
```

---

## Integration Notes

1. **Backend Dependency:** Most endpoints proxy requests to the FastAPI backend at `http://localhost:8000`
2. **Timeout Handling:** Workout generation has a 10-minute timeout
3. **Input Validation:** All user inputs are validated before forwarding to backend
4. **Error Propagation:** Backend errors are properly formatted and returned to client
5. **ExerciseDB Integration:** Exercise data is fetched from ExerciseDB API and cached in vector store

---

## See Also

- [ExerciseDB API Schema](./EXERCISEDB_API_SCHEMA.md) - Complete ExerciseDB API reference
- [README.md](./README.md) - Project setup and configuration
- FastAPI Backend Documentation: http://localhost:8000/docs

---

*Last Updated: 2026-05-31*