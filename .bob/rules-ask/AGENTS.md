# Project Documentation Context (Non-Obvious Only)

- **`flask/`** is the UI frontend, not the API server. It acts as a launcher that spawns the FastAPI process (`flask/utils/ServerManager`) and then serves the HTML frontend on port 7500.
- **`fastapiserver/`** is the sole API backend (port 7501); `flask/` has no business logic.
- **Two separate `requirements.txt`** exist: root (`requirements.txt`) for the FastAPI server and `flask/requirements.txt` for the Flask frontend only.
- **The only runnable test** is `test_api_format.py` at the project root — it validates JSON serialisation format, not API behaviour.
- **`failed_parse.json`** in the project root is a debug artefact written automatically when LLM JSON parsing fails; it is not a fixture or config file.
- **`ANDROID_API_GUIDE.md`** describes how to consume the API from an Android client — useful when understanding the expected JSON contract.
- **ChromaDB collection name** is hardcoded as `"exercise_embeddings"` in `VectorStoreService.initialize_collection()`.
- **LLM model auto-resolution** happens silently at request time when `LLM_MODEL` is blank; see `ServiceFactory._resolve_model()` for the fallback chain.
- **3-tab model selection**: the Flask UI uses `POST /api/fetch-models` to load model dropdowns (local and online providers) and `POST /api/validate-model` for GGUF path checks only. The legacy `GET/POST /api/models` endpoint exists but is not used by the current UI.
- **`WorkoutDay`** fields are `groupName`, `isAiGenerated`, `selectedExercises`; `workout_days` is only the LLM prompt/response key and is never exposed in the final API response (`workoutGroups`).
