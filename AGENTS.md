# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Stack
- **FastAPI** backend (`fastapiserver/`) on port 7501; **Flask** frontend (`flask/`) on port 7500
- Python 3.11, Pydantic v2, ChromaDB, sentence-transformers, OpenAI SDK
- GGUF via llama-cpp-python, or any OpenAI-compatible server (local or public API)

## Running the App

```bash
# Local (starts both Flask frontend + FastAPI backend)
python flask/app.py

# FastAPI only
uvicorn fastapiserver.main:app --host 0.0.0.0 --port 7501 --reload

# Docker (Colima)
docker compose up --build
```

## Testing
No pytest suite. The only test file is `test_api_format.py` — run it directly:
```bash
python test_api_format.py
```
Failed LLM parse responses are dumped to `failed_parse.json` in the project root for debugging.

## Configuration
- All settings live in `.env` (copy `.env.example`). Settings are loaded via `get_settings()` in `fastapiserver/config.py` — it is `@lru_cache`-decorated; changing `.env` at runtime has no effect without a restart.
- In Docker, `LLM_BASE_URL` is overridden by `LLM_BASE_URL_DOCKER` (`host.docker.internal` address). Both must be set in `.env`.
- Vector DB persists at `CHROMA_DB_PATH` (default `./data/chroma_db`). To rebuild: `rm -rf ./data/chroma_db`.

## LLM Service Architecture
- All LLM backends (`LLMService`, `GGUFService`) are created **lazily** via `ServiceFactory.create_service()` — never directly instantiated in endpoints.
- After each `/api/v1/generate` request, the service is explicitly cleaned up (GGUF `del`+`gc.collect()`). Caching is **disabled** at the generate endpoint (`use_cache=False`).
- When `LLM_MODEL` is blank, `ServiceFactory._resolve_model()` auto-queries `GET {base_url}/models` and picks the first result.
- OMLX auth quirk: send no `Authorization` header (`api_key=None`) when `LLM_API_KEY` is unset. Sending `lm-studio` as a fallback key will break OMLX's `verify_api_key()`. See `LLMService.__init__` for the detection logic (port `:8000` == OMLX).

## Flask 3-Tab Model Selection (UI → Backend)
- **GGUF tab**: path validated server-side via `POST /api/validate-model` (checks `.gguf` extension + `os.path.exists`)
- **Local Provider tab**: Flask fetches models from `POST /api/fetch-models` with `provider_type=local`; queries `{base_url}/models`
- **Online Provider tab**: Flask fetches models from `POST /api/fetch-models` with `provider_type=online`
  - Anthropic has **no `/models` endpoint** — key is verified via a 1-token `POST /messages` call; a static curated list is returned
  - Gemini base URL: `https://generativelanguage.googleapis.com/v1beta/openai` (OpenAI-compatible)
- Legacy `/api/models` endpoint is kept but should not be extended

## Data Models — Non-Obvious Details
- `Exercise.description` stores instruction steps **joined with ` $$ `** as separator — not a list.
- `WorkoutDay` fields are `groupName`, `isAiGenerated`, `selectedExercises` — not `day_name`/`exercises`.
- `WorkoutPlan` wraps `workoutGroups: List[WorkoutDay]`; old `workout_days` key is only used inside the LLM prompt/response cycle and is converted before returning to callers.
- `WorkoutGenerationRequest` wraps `user_profile` + optional `llm_config` — the endpoint accepts both as a single JSON body.
- `ModelConfig` uses `class Config: protected_namespaces = ()` to allow fields named `model_*`.
- Pydantic validators use `@validator` (v1-style) despite the project running Pydantic v2.

## JSON Parsing
- `parse_llm_json_response()` in `fastapiserver/utils/json_parser.py` must be used for all LLM output — it handles markdown code-blocks, brace-matching, extra-data errors, and repair. Never use `json.loads()` directly on LLM responses.

## Logging
- `setup_structured_logging()` must be called before any logger usage. Request IDs flow through `ContextVar` (`request_id_var`); add `RequestIDFilter` to handlers to include them in log records.
- Set `USE_JSON_LOGGING=true` (env) for production JSON logs; default is human-readable format.

## Import Order Convention
```python
# Standard library
# Third-party
# Local application (fastapiserver.*)
```

## Code Style
- All files end with `# Made with Bob` comment.
- Module-level docstrings on every file.
- `logger = logging.getLogger(__name__)` at module top.
- Enums extend `(str, Enum)` for JSON serialisation compatibility.
