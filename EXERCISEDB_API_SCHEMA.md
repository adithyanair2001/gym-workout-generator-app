# ExerciseDB API Schema

Complete API reference for ExerciseDB V1 API integration.

**Base URL**: `https://oss.exercisedb.dev`  
**Version**: v1.0.0  
**Authentication**: API Key required (via `X-API-Key` header)

## 📋 Available Endpoints

### 1. **Liveness Check**
Check API service status.

```
GET /api/v1/liveness
```

**Response**: `200 OK`
```json
{
  "status": "string"
}
```

---

### 2. **List All Exercises**
Retrieve all exercises with pagination.

```
GET /api/v1/exercises
```

**Query Parameters**:
- `limit` (integer): Maximum results to return (min: 1, max: 25, default: 10)
- `after` (string): Exercise ID to paginate after (forward pagination)
- `before` (string): Exercise ID to paginate before (backward pagination)

**Response**: `200 OK`
```json
[
  {
    "id": "string",
    "name": "string",
    "gifUrl": "string",
    "targetMuscles": ["string"],
    "bodyParts": ["string"],
    "equipments": ["string"],
    "secondaryMuscles": ["string"],
    "instructions": ["string"]
  }
]
```

---

### 3. **Advanced Exercise Search**
Filter exercises by multiple criteria with fuzzy search.

```
GET /api/v1/exercises/search
```

**Query Parameters**:
- `name` (string): Exercise name (supports fuzzy matching)
- `targetMuscles` (string): Target muscles (comma-separated for multiple)
- `bodyParts` (string): Body parts (comma-separated for multiple)
- `equipments` (string): Required equipment (comma-separated for multiple)
- `limit` (integer): Maximum results (min: 1, max: 25, default: 10)
- `after` (string): Exercise ID for forward pagination
- `before` (string): Exercise ID for backward pagination

**Response**: `200 OK`
```json
[
  {
    "id": "string",
    "name": "string",
    "gifUrl": "string",
    "targetMuscles": ["string"],
    "bodyParts": ["string"],
    "equipments": ["string"],
    "secondaryMuscles": ["string"],
    "instructions": ["string"]
  }
]
```

---

### 4. **Get Exercise by ID**
Retrieve a specific exercise by its ID.

```
GET /api/v1/exercises/{exerciseId}
```

**Path Parameters**:
- `exerciseId` (string, required): Unique exercise identifier

**Response**: `200 OK`
```json
{
  "id": "string",
  "name": "string",
  "gifUrl": "string",
  "targetMuscles": ["string"],
  "bodyParts": ["string"],
  "equipments": ["string"],
  "secondaryMuscles": ["string"],
  "instructions": ["string"]
}
```

---

### 5. **List Body Parts**
Get all available body parts.

```
GET /api/v1/exercises/bodyparts
```

**Response**: `200 OK`
```json
["string"]
```

---

### 6. **List Target Muscles**
Get all available target muscles.

```
GET /api/v1/exercises/muscles
```

**Response**: `200 OK`
```json
["string"]
```

---

### 7. **List Equipment Types**
Get all available equipment types.

```
GET /api/v1/exercises/equipments
```

**Response**: `200 OK`
```json
["string"]
```

---

### 8. **List Body Parts (Alternative)**
Get all body parts (alternative endpoint).

```
GET /api/v1/bodyparts
```

**Response**: `200 OK`
```json
["string"]
```

---

## 🔑 Authentication

All requests require an API key in the header:

```
X-API-Key: your_api_key_here
```

---

## 📊 Response Codes

| Code | Description |
|------|-------------|
| 200 | Success - Request completed successfully |
| 400 | Bad Request - Malformed request or invalid parameters |
| 401 | Unauthorized - Missing or invalid API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 412 | Precondition Failed - Required conditions not met |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error occurred |

---

## 🎯 Usage Examples

### Example 1: Get All Exercises (Paginated)
```bash
curl -X GET "https://oss.exercisedb.dev/api/v1/exercises?limit=10" \
  -H "X-API-Key: your_api_key"
```

### Example 2: Search by Target Muscle
```bash
curl -X GET "https://oss.exercisedb.dev/api/v1/exercises/search?targetMuscles=pectorals&limit=5" \
  -H "X-API-Key: your_api_key"
```

### Example 3: Search by Equipment
```bash
curl -X GET "https://oss.exercisedb.dev/api/v1/exercises/search?equipments=barbell,dumbbell&limit=10" \
  -H "X-API-Key: your_api_key"
```

### Example 4: Get Specific Exercise
```bash
curl -X GET "https://oss.exercisedb.dev/api/v1/exercises/0001" \
  -H "X-API-Key: your_api_key"
```

### Example 5: List All Body Parts
```bash
curl -X GET "https://oss.exercisedb.dev/api/v1/exercises/bodyparts" \
  -H "X-API-Key: your_api_key"
```

---

## 📝 Exercise Object Schema

```typescript
interface Exercise {
  id: string;                    // Unique identifier
  name: string;                  // Exercise name
  gifUrl: string;                // 180p GIF URL for visual demonstration
  targetMuscles: string[];       // Primary target muscles
  bodyParts: string[];           // Body parts involved
  equipments: string[];          // Required equipment
  secondaryMuscles: string[];    // Secondary muscles worked
  instructions: string[];        // Step-by-step instructions
}
```

---

## ⚠️ Rate Limits

- **Free Version**: Strict rate limits apply
- **Attribution Required**: Credit to AscendAPI required when using this dataset
- **Commercial Use**: Requires paid plan via RapidAPI

---

## 🔗 Useful Links

- **Documentation**: https://docs.ascendapi.com
- **Website**: https://ascendapi.com
- **RapidAPI**: Subscribe for commercial use
- **GitHub**: https://github.com/exercisedb
- **Support**: support@ascendapi.com

---

## 📦 Dataset Features

- **1,500+ Structured Exercises**: Comprehensive dataset
- **Rich Metadata**: Target muscles, equipment, body parts
- **Visual Aids**: 180p GIF-based demonstrations
- **Step-by-Step Instructions**: Clear guidance for proper form
- **Fuzzy Search**: Flexible search capabilities
- **Cursor-based Pagination**: Efficient data retrieval

---

## 🎨 Integration Notes

1. **Pagination**: Use `after`/`before` cursors for efficient pagination
2. **Fuzzy Search**: Name parameter supports partial matching
3. **Multiple Filters**: Combine filters with comma-separated values
4. **Rate Limiting**: Implement exponential backoff for 429 responses
5. **Caching**: Cache responses to minimize API calls
6. **Error Handling**: Handle all response codes gracefully

---

**Last Updated**: 2026-05-31  
**API Version**: v1.0.0