# Project Architecture Constraints (Non-Obvious Only)

- **Flask is a process supervisor, not just a web server.** `flask/utils/ServerManager` starts the FastAPI subprocess. Any architecture change that separates the two processes must account for this launcher pattern.
- **Vector store is populated once at startup** (only when `count() == 0`). Subsequent starts skip the ExerciseDB fetch entirely. Schema or content changes require `rm -rf ./data/chroma_db` before restarting.
- **Docker/local URL duality**: `LLM_BASE_URL` is for local runs; `LLM_BASE_URL_DOCKER` overrides it inside Docker. `docker-compose.yml` injects `LLM_BASE_URL=${LLM_BASE_URL_DOCKER}` so the app always reads `llm_base_url`. Any new environment-dependent URL config must follow this two-variable pattern.
- **Rate limiting is IP-based via slowapi** (`5/minute` on `/api/v1/generate`). The limiter key function is `get_remote_address` — behind a reverse proxy, `X-Forwarded-For` must be trusted or all traffic appears as one IP.
- **Middleware execution order** (outermost → innermost): CORS → GZip → RequestID. New middleware must be added with this ordering in mind (last `add_middleware` call runs first).
- **`WorkoutPlan.workoutGroups`** is the canonical response key. The LLM is prompted to produce `workout_days`; this is converted before returning to callers. Never expose `workout_days` in the API response.
- **ChromaDB batching**: embeddings are generated in batches of 32. Changing batch size affects both memory usage and progress logging granularity.
- **`LLMService` retry policy**: only `APIConnectionError`, `APITimeoutError`, and `RateLimitError` are retried (max 3 attempts, exponential backoff 2^attempt seconds). `APIError` (bad request etc.) is not retried. Plan new LLM call sites accordingly.
- **Anthropic integration** has no `/models` endpoint — key verification uses a 1-token `POST /messages` call; a static curated list is returned. Any new online provider that lacks a `/models` endpoint must follow the same pattern in `flask/api/routes.py::_fetch_online_models`.
