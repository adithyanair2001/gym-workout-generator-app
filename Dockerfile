# Gym Workout RAG - Multi-stage Docker Build
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for vector database
RUN mkdir -p data/chroma_db

# Expose ports
# 7500 - Flask Frontend
# 7501 - FastAPI Backend
EXPOSE 7500 7501

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7501/health || exit 1

# Run the Flask app (which auto-starts FastAPI)
CMD ["python", "flask/app.py"]

# Made with Bob
