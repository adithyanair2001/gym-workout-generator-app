# Android App API Integration Guide

Complete guide for integrating your Android app with the Gym Workout RAG Flask server.

## 🎯 Overview

Your Android app can call the Flask server to generate personalized workout plans. The server will:
1. Receive user profile and exercise preferences
2. Load the appropriate LLM model (if not already loaded)
3. Generate a personalized workout plan using RAG
4. Return JSON workout data in Android-compatible format
5. Automatically unload the model to free memory

## 📡 API Endpoint

**Base URL:** `http://YOUR_SERVER_IP:7500`

**Endpoint:** `POST /api/generate`

**Content-Type:** `application/json`

## 📥 Request Format

### Required Fields

```json
{
  "height": 175.0,
  "weight": 70.0,
  "age": 25,
  "gender": "male",
  "fitness_level": "intermediate",
  "days_per_week": 4,
  "session_duration": 60,
  "goals": ["muscle_gain", "strength"],
  "equipment": ["barbell", "dumbbell", "bench"],
  "preferred_split": "push_pull_legs"
}
```

### Optional Fields

```json
{
  "injuries": "lower back pain",
  "model_config": {
    "model_type": "local_server",
    "llm_base_url": "http://127.0.0.1:1234/v1",
    "llm_model": "llama-3.2-3b-instruct"
  }
}
```

## 📤 Response Format

### Success Response (200 OK)

```json
{
  "success": true,
  "workout_plan": {
    "workoutGroups": [
      {
        "groupName": "Day 1: Push (Chest, Shoulders, Triceps)",
        "isAiGenerated": true,
        "selectedExercises": [
          {
            "exerciseDbId": "EIeI8Vf",
            "exerciseName": "barbell bench press",
            "bodyPart": "Chest",
            "equipments": "Barbell",
            "targetMuscles": "pectorals",
            "secondaryMuscles": "shoulders,triceps",
            "mediaUrl": "https://static.exercisedb.dev/media/EIeI8Vf.gif",
            "description": "Lie flat on bench $$ Grip barbell slightly wider than shoulders $$ Lower to chest with control $$ Press back up to starting position"
          }
        ]
      }
    ],
    "metadata": {
      "model_provider": "lm_studio",
      "model_name": "llama-3.2-3b-instruct",
      "generated_at": "2026-06-24T20:07:30.123456",
      "workout_groups_count": 3
    }
  }
}
```

### Metadata Fields

The `metadata` object provides information about the model used to generate the workout plan:

| Field | Type | Description |
|-------|------|-------------|
| `model_provider` | string | The LLM provider used (e.g., "lm_studio", "ollama", "openai", "anthropic", "groq", "mlx", "gguf") |
| `model_name` | string | The specific model name used for generation |
| `generated_at` | string | ISO 8601 timestamp of when the plan was generated |
| `workout_groups_count` | int | Total number of workout groups in the plan |

**Model Provider Values:**
- `"lm_studio"` - LM Studio (local server on port 1234)
- `"ollama"` - OLLAMA (local server on port 11434 or 8001)
- `"omlx"` - OMLX (local server on port 8000)
- `"local_server"` - Other local server
- `"openai"` - OpenAI GPT models
- `"anthropic"` - Anthropic Claude
- `"groq"` - Groq API
- `"mlx"` - MLX models (Mac only)
- `"gguf"` - GGUF models
- `"api"` - Generic API provider

### Error Response (4xx/5xx)

```json
{
  "success": false,
  "message": "Validation error: height must be between 100 and 250 cm"
}
```

## 🔧 Field Specifications

### User Profile Fields

| Field | Type | Required | Valid Values | Description |
|-------|------|----------|--------------|-------------|
| `height` | float | Yes | 100-250 | Height in cm |
| `weight` | float | Yes | 30-300 | Weight in kg |
| `age` | int | Yes | 13-100 | Age in years |
| `gender` | string | Yes | "male", "female", "other" | Gender |
| `fitness_level` | string | Yes | "beginner", "intermediate", "advanced" | Fitness level |
| `days_per_week` | int | Yes | 1-7 | Workout days per week |
| `session_duration` | int | Yes | 15-180 | Session duration in minutes |
| `goals` | array/string | Yes | See below | Fitness goals |
| `equipment` | array/string | Yes | See below | Available equipment |
| `injuries` | string | No | Any text | Injuries or limitations |
| `preferred_split` | string | No | See below | Workout split preference |

### Valid Goals

- `"muscle_gain"` - Build muscle mass
- `"strength"` - Increase strength
- `"weight_loss"` - Lose weight
- `"endurance"` - Improve endurance
- `"flexibility"` - Increase flexibility
- `"general_fitness"` - Overall fitness

**Format:** Can be array `["muscle_gain", "strength"]` or comma-separated string `"muscle_gain,strength"`

### Valid Equipment

- `"barbell"` - Barbell
- `"dumbbell"` - Dumbbells
- `"bodyweight"` - Bodyweight only
- `"bench"` - Bench
- `"cable"` - Cable machine
- `"machine"` - Weight machines
- `"kettlebell"` - Kettlebells
- `"resistance_band"` - Resistance bands

**Format:** Can be array `["barbell", "dumbbell"]` or comma-separated string `"barbell,dumbbell"`

### Valid Workout Splits

- `"full_body"` - Full body workouts
- `"upper_lower"` - Upper/lower split
- `"push_pull_legs"` - Push/pull/legs split
- `"auto"` - Automatically determine based on days per week (default)

### Model Configuration (Optional)

If you want to specify which LLM to use, include `model_config`:

```json
{
  "model_config": {
    "model_type": "local_server",
    "llm_base_url": "http://127.0.0.1:1234/v1",
    "llm_model": "llama-3.2-3b-instruct"
  }
}
```

**Model Types:**
- `"local_server"` - LM Studio or OLLAMA
- `"openai"` - OpenAI GPT models
- `"anthropic"` - Anthropic Claude
- `"groq"` - Groq API
- `"mlx"` - MLX models (Mac only)
- `"gguf"` - GGUF models

If omitted, server uses `.env` configuration.

## 📱 Android Implementation Examples

### Using Retrofit (Kotlin)

```kotlin
// API Interface
interface WorkoutApi {
    @POST("api/generate")
    suspend fun generateWorkout(
        @Body request: WorkoutRequest
    ): Response<WorkoutResponse>
}

// Data Classes
data class WorkoutRequest(
    val height: Float,
    val weight: Float,
    val age: Int,
    val gender: String,
    val fitness_level: String,
    val days_per_week: Int,
    val session_duration: Int,
    val goals: List<String>,
    val equipment: List<String>,
    val injuries: String? = null,
    val preferred_split: String = "auto",
    val model_config: ModelConfig? = null
)

data class ModelConfig(
    val model_type: String,
    val llm_base_url: String,
    val llm_model: String
)

data class WorkoutResponse(
    val success: Boolean,
    val workout_plan: WorkoutPlan?,
    val message: String?
)

data class WorkoutPlan(
    val workoutGroups: List<WorkoutGroup>,
    val metadata: WorkoutMetadata
)

data class WorkoutMetadata(
    val model_provider: String,
    val model_name: String,
    val generated_at: String,
    val workout_groups_count: Int
)

data class WorkoutGroup(
    val groupName: String,
    val isAiGenerated: Boolean,
    val selectedExercises: List<Exercise>
)

data class Exercise(
    val exerciseDbId: String,
    val exerciseName: String,
    val bodyPart: String,
    val equipments: String,
    val targetMuscles: String,
    val secondaryMuscles: String,
    val mediaUrl: String,
    val description: String
)

// Usage
class WorkoutRepository(private val api: WorkoutApi) {
    suspend fun generateWorkout(
        height: Float,
        weight: Float,
        age: Int,
        gender: String,
        fitnessLevel: String,
        daysPerWeek: Int,
        sessionDuration: Int,
        goals: List<String>,
        equipment: List<String>
    ): Result<WorkoutPlan> {
        return try {
            val request = WorkoutRequest(
                height = height,
                weight = weight,
                age = age,
                gender = gender,
                fitness_level = fitnessLevel,
                days_per_week = daysPerWeek,
                session_duration = sessionDuration,
                goals = goals,
                equipment = equipment
            )
            
            val response = api.generateWorkout(request)
            
            if (response.isSuccessful && response.body()?.success == true) {
                Result.success(response.body()!!.workout_plan!!)
            } else {
                Result.failure(Exception(response.body()?.message ?: "Unknown error"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```

### Using OkHttp (Java)

```java
public class WorkoutApiClient {
    private static final String BASE_URL = "http://YOUR_SERVER_IP:7500";
    private final OkHttpClient client = new OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(600, TimeUnit.SECONDS) // 10 minutes for generation
        .build();
    
    public void generateWorkout(
        float height,
        float weight,
        int age,
        String gender,
        String fitnessLevel,
        int daysPerWeek,
        int sessionDuration,
        List<String> goals,
        List<String> equipment,
        WorkoutCallback callback
    ) {
        JSONObject json = new JSONObject();
        try {
            json.put("height", height);
            json.put("weight", weight);
            json.put("age", age);
            json.put("gender", gender);
            json.put("fitness_level", fitnessLevel);
            json.put("days_per_week", daysPerWeek);
            json.put("session_duration", sessionDuration);
            json.put("goals", new JSONArray(goals));
            json.put("equipment", new JSONArray(equipment));
            json.put("preferred_split", "auto");
            
            RequestBody body = RequestBody.create(
                json.toString(),
                MediaType.parse("application/json")
            );
            
            Request request = new Request.Builder()
                .url(BASE_URL + "/api/generate")
                .post(body)
                .build();
            
            client.newCall(request).enqueue(new Callback() {
                @Override
                public void onResponse(Call call, Response response) {
                    try {
                        String responseBody = response.body().string();
                        JSONObject jsonResponse = new JSONObject(responseBody);
                        
                        if (jsonResponse.getBoolean("success")) {
                            JSONObject workoutPlan = jsonResponse.getJSONObject("workout_plan");
                            callback.onSuccess(workoutPlan);
                        } else {
                            callback.onError(jsonResponse.getString("message"));
                        }
                    } catch (Exception e) {
                        callback.onError(e.getMessage());
                    }
                }
                
                @Override
                public void onFailure(Call call, IOException e) {
                    callback.onError(e.getMessage());
                }
            });
        } catch (JSONException e) {
            callback.onError(e.getMessage());
        }
    }
    
    public interface WorkoutCallback {
        void onSuccess(JSONObject workoutPlan);
        void onError(String error);
    }
}
```

## 🔒 Security Considerations

### For Production

1. **Use HTTPS:** Deploy with SSL certificate
   ```
   https://your-domain.com:7500/api/generate
   ```

2. **Add Authentication:** Implement API key or JWT tokens
   ```kotlin
   @Headers("Authorization: Bearer YOUR_API_KEY")
   ```

3. **Rate Limiting:** Server has built-in rate limiting (5 requests/minute per IP)

4. **Input Validation:** Server validates all inputs, but validate on client too

### Network Security Config (Android)

For development with HTTP:

```xml
<!-- res/xml/network_security_config.xml -->
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">YOUR_SERVER_IP</domain>
        <domain includeSubdomains="true">localhost</domain>
    </domain-config>
</network-security-config>
```

```xml
<!-- AndroidManifest.xml -->
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ...>
```

## 🧪 Testing

### Test with cURL

```bash
curl -X POST http://localhost:7500/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "height": 175,
    "weight": 70,
    "age": 25,
    "gender": "male",
    "fitness_level": "intermediate",
    "days_per_week": 4,
    "session_duration": 60,
    "goals": ["muscle_gain", "strength"],
    "equipment": ["barbell", "dumbbell", "bench"],
    "preferred_split": "push_pull_legs"
  }'
```

### Test with Postman

1. Method: POST
2. URL: `http://YOUR_SERVER_IP:7500/api/generate`
3. Headers: `Content-Type: application/json`
4. Body: Raw JSON (see example above)

## ⚡ Performance Tips

1. **Timeout:** Set read timeout to at least 10 minutes (600 seconds)
2. **Caching:** Cache workout plans locally to reduce API calls
3. **Background Thread:** Always call API on background thread
4. **Progress Indicator:** Show loading indicator (generation takes 30-60 seconds)
5. **Retry Logic:** Implement exponential backoff for failed requests

## 🐛 Common Errors

| Status Code | Error | Solution |
|-------------|-------|----------|
| 400 | Validation error | Check all required fields and valid values |
| 503 | Cannot connect to backend | Ensure FastAPI server is running on port 7501 |
| 504 | Request timeout | Model is too slow, try smaller model or LM Studio |
| 500 | Internal server error | Check server logs for details |

## 📊 Response Data Structure

The `description` field contains instructions separated by `$$`:

```
"Lie flat on bench $$ Grip barbell $$ Lower to chest $$ Press back up"
```

Parse in Android:
```kotlin
val instructions = exercise.description.split("$$").map { it.trim() }
```

## 🔄 Model Management

The server automatically:
1. Loads model when first request arrives
2. Generates workout plan
3. Unloads model after generation to free memory

You can also manually unload:
```bash
curl -X POST http://localhost:7501/api/v1/models/unload
```

## 📞 Support Endpoints

### Health Check
```bash
GET http://localhost:7500/api/health
```

Returns server status and configuration.

### List Available Models (LM Studio)
```bash
POST http://localhost:7500/api/models
Content-Type: application/json

{
  "base_url": "http://127.0.0.1:1234/v1"
}
```

Returns list of loaded models in LM Studio.

---

**Made with Bob**