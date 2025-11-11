# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files into container
COPY . /app

# Install dependencies and ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python packages
RUN pip install --upgrade pip
RUN pip install --no-cache-dir openai moviepy pillow python-dotenv requests selenium

# Expose optional port (Coolify friendly)
EXPOSE 3000

# Run main script
CMD ["python", "main.py"]
