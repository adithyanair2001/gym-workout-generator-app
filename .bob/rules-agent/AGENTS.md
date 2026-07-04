# Project Coding Rules (Non-Obvious Only)

- **Never instantiate LLM services directly** — always use `ServiceFactory.create_service()` (`fastapiserver/services/service_factory.py`). Pass `use_cache=False` in request handlers so models are cleaned up after use.
- **Always use `parse_llm_json_response()`** from `fastapiserver/utils/json_parser.py` for any LLM output; raw `json.loads()` will fail on model responses that include markdown fences or extra text.
- **Exercise description** uses ` $$ ` as the instruction-step separator, not `\n` or a list. Construct and parse accordingly.
- **`WorkoutDay` field names** are `groupName`, `isAiGenerated`, `selectedExercises` — not `day_name`/`exercises`. `workout_days` is an internal LLM prompt key only, never returned in the API response.
- **`get_settings()` is `@lru_cache`d** — never mutate returned settings; changes to `.env` require a process restart.
- **Pydantic v1-style `@validator`** is used project-wide despite Pydantic v2 being installed. Do not switch to `@field_validator`.
- **`ModelConfig` must keep `protected_namespaces = ()`** — removing it breaks fields named `model_*`.
- **OMLX auth quirk**: `LLMService.__init__` detects OMLX by port `:8000` in the base URL and passes `api_key=None` when no key is configured, skipping the `Authorization` header entirely. Sending `lm-studio` as a fallback key will fail OMLX's `verify_api_key()`.
- **Anthropic `/fetch-models` returns a static list** — there is no Anthropic `/models` endpoint; the key is verified with a 1-token `POST /messages` call and a hardcoded curated list is returned.
- **Gemini** uses `https://generativelanguage.googleapis.com/v1beta/openai` as its OpenAI-compatible base URL — not the standard `https://api.gemini.com`.
- **End every file** with `# Made with Bob` comment on the last line.
- **Import order**: stdlib → third-party → `fastapiserver.*` local imports.
- All enums must extend `(str, Enum)` for transparent JSON serialisation.
