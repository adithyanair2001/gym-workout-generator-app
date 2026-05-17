# OMLX Setup Guide

## What is OMLX?

OMLX (OpenAI MLX) is an OpenAI-compatible server for MLX models. It provides a REST API that mimics OpenAI's API, making it easy to use MLX models with any OpenAI-compatible client.

**Repository**: https://github.com/jundot/omlx

## Benefits

- ✅ **OpenAI-Compatible API**: Works with any OpenAI client library
- ✅ **MLX Models**: Run Apple Silicon optimized models locally
- ✅ **No API Costs**: Free local inference
- ✅ **Fast**: Optimized for Apple Silicon (M1/M2/M3)
- ✅ **Easy Integration**: Drop-in replacement for OpenAI API

## Installation

### Step 1: Install OMLX

```bash
# Install via pip
pip install omlx

# Or install from source
git clone https://github.com/jundot/omlx.git
cd omlx
pip install -e .
```

### Step 2: Download MLX Models

OMLX works with MLX-format models from Hugging Face:

```bash
# Example: Download Qwen 2.5 7B
huggingface-cli download mlx-community/Qwen2.5-7B-Instruct-4bit

# Example: Download Llama 3.2 3B
huggingface-cli download mlx-community/Llama-3.2-3B-Instruct-4bit

# Example: Download Qwen 3.5 4B (Recommended)
huggingface-cli download mlx-community/Qwen3.5-4B-MLX-4bit
```

Models are downloaded to: `~/.cache/huggingface/hub/`

### Step 3: Start OMLX Server

```bash
# Start server with default settings (port 8000)
omlx serve --model mlx-community/Qwen3.5-4B-MLX-4bit

# Start on custom port
omlx serve --model mlx-community/Qwen3.5-4B-MLX-4bit --port 8001

# With custom host
omlx serve --model mlx-community/Qwen3.5-4B-MLX-4bit --host 0.0.0.0 --port 8001

# With GPU layers (for acceleration)
omlx serve --model mlx-community/Qwen3.5-4B-MLX-4bit --n-gpu-layers 32
```

### Step 4: Configure Gym Workout RAG

Update your `.env` file:

```bash
# Use OMLX server
USE_MLX=false
USE_GGUF=false

# OMLX server URL (default port 8000)
LLM_BASE_URL=http://127.0.0.1:8000/v1

# Model name (use the model you started OMLX with)
LLM_MODEL=mlx-community/Qwen3.5-4B-MLX-4bit

# No API key needed for local OMLX
LLM_API_KEY=

# LLM parameters
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=32000
```

### Step 5: Start Gym Workout RAG

```bash
# Start the application
python frontend/app.py
```

## OMLX vs Direct MLX

| Feature | OMLX | Direct MLX (use_mlx=true) |
|---------|------|---------------------------|
| **API** | OpenAI-compatible REST API | Direct Python integration |
| **Setup** | Separate server process | Built into app |
| **Flexibility** | Can use from any language | Python only |
| **Agent Mode** | No (RAG only) | Yes (with tool calling) |
| **Performance** | Slight HTTP overhead | Direct, no overhead |
| **Use Case** | Multiple clients, microservices | Single app, agent workflows |

## Recommended Models for OMLX

### Small & Fast (< 5GB)
- `mlx-community/Llama-3.2-3B-Instruct-4bit` (1.7GB)
- `mlx-community/Qwen3.5-4B-MLX-4bit` (2.5GB) ⭐ **Recommended**

### Medium (5-10GB)
- `mlx-community/Qwen3.5-9B-MLX-4bit` (5.6GB)
- `mlx-community/Llama-3.1-8B-Instruct-4bit` (4.9GB)

### Large (> 10GB)
- `mlx-community/Qwen3.6-27B-4bit` (15GB)
- `mlx-community/Llama-3.1-70B-Instruct-4bit` (40GB)

## Testing OMLX

### Test with curl

```bash
# Test chat completion
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Qwen3.5-4B-MLX-4bit",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7
  }'
```

### Test with Python

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="mlx-community/Qwen3.5-4B-MLX-4bit",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Use a different port
omlx serve --model mlx-community/Qwen3.5-4B-MLX-4bit --port 8001

# Update .env
LLM_BASE_URL=http://127.0.0.1:8001/v1
```

### Model Not Found

```bash
# List downloaded models
ls ~/.cache/huggingface/hub/

# Download model if missing
huggingface-cli download mlx-community/Qwen3.5-4B-MLX-4bit
```

### Slow Performance

```bash
# Enable GPU acceleration
omlx serve --model mlx-community/Qwen3.5-4B-MLX-4bit --n-gpu-layers 32

# Use a smaller model
omlx serve --model mlx-community/Llama-3.2-3B-Instruct-4bit
```

## Advanced Configuration

### Custom System Prompt

```bash
omlx serve \
  --model mlx-community/Qwen3.5-4B-MLX-4bit \
  --system-prompt "You are a helpful fitness assistant."
```

### Context Window

```bash
# Increase context window (default: 4096)
omlx serve \
  --model mlx-community/Qwen3.5-4B-MLX-4bit \
  --max-tokens 8192
```

### Multiple Models

Run multiple OMLX servers on different ports:

```bash
# Terminal 1: Small fast model
omlx serve --model mlx-community/Llama-3.2-3B-Instruct-4bit --port 8000

# Terminal 2: Larger quality model
omlx serve --model mlx-community/Qwen3.5-9B-MLX-4bit --port 8001
```

## Integration with Gym Workout RAG

### Option 1: OMLX Server (Recommended for Production)

```bash
# .env
USE_MLX=false
LLM_BASE_URL=http://127.0.0.1:8000/v1
LLM_MODEL=mlx-community/Qwen3.5-4B-MLX-4bit
```

**Pros:**
- Separate process, easier to manage
- Can restart model without restarting app
- OpenAI-compatible, works with any client

**Cons:**
- No agent mode (tool calling)
- Slight HTTP overhead

### Option 2: Direct MLX (Recommended for Development)

```bash
# .env
USE_MLX=true
MLX_MODEL_PATH=/Users/username/.lmstudio/models/mlx-community/Qwen3.5-4B-MLX-4bit
```

**Pros:**
- Agent mode with tool calling
- Direct integration, no HTTP overhead
- Simpler setup (no separate server)

**Cons:**
- Python only
- Model loaded in app memory

## Resources

- **OMLX GitHub**: https://github.com/jundot/omlx
- **MLX Models**: https://huggingface.co/mlx-community
- **MLX Documentation**: https://ml-explore.github.io/mlx/
- **OpenAI API Docs**: https://platform.openai.com/docs/api-reference

## Quick Start Commands

```bash
# 1. Install OMLX
pip install omlx

# 2. Download model
huggingface-cli download mlx-community/Qwen3.5-4B-MLX-4bit

# 3. Start OMLX server
omlx serve --model mlx-community/Qwen3.5-4B-MLX-4bit --port 8001

# 4. Update .env
echo "USE_MLX=false" >> .env
echo "LLM_BASE_URL=http://127.0.0.1:8001/v1" >> .env
echo "LLM_MODEL=mlx-community/Qwen3.5-4B-MLX-4bit" >> .env

# 5. Start app
python frontend/app.py
```

---

**Made with Bob**