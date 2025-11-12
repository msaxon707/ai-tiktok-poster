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
ENV ASSETS_DIR=/app/assets \
    VIDEOS_DIR=/app/videos \
    OUTPUT_PATH=/app/output \
    MAX_POSTS_PER_DAY=6 \
    MAX_POSTS_PER_RUN=1

CMD ["python", "main.py"]

