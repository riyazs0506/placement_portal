# ================================================================
# Dockerfile — University Placement Portal (FINAL FIXED)
# ================================================================
FROM python:3.11.9-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libssl-dev libffi-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Upgrade pip tools
RUN pip install --upgrade pip setuptools wheel

# Install pydantic (binary only → avoids Rust)
RUN pip install --no-cache-dir --only-binary=:all: \
    pydantic-core==2.18.2 \
    pydantic==2.7.1

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install performance libs (Linux only)
RUN pip install --no-cache-dir uvloop httptools

# Copy project files
COPY . .

# Create required folders
RUN mkdir -p uploads static/css static/js templates

# Render uses dynamic PORT → don't hardcode 8000
EXPOSE 10000

# Health check (Render compatible)
HEALTHCHECK CMD curl --fail http://localhost:$PORT/health || exit 1

# Start app (IMPORTANT FIX HERE)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2 --loop uvloop --http httptools --log-level info"]