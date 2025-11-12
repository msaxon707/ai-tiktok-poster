# Dockerfile
FROM python:3.11-slim

# System deps for moviepy / ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Default env dirs (can be overridden in Coolify)
ENV CONFIG_FILE=/app/config.txt \
    DATA_ROOT=/data \
    LOG_LEVEL=INFO
    CMD ["python", "cli.py", "schedule"]
