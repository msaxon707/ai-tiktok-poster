FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy all files
COPY . /app

# Install system dependencies required for moviepy
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Show installed packages (for debug)
RUN pip list

# Run script
CMD ["python", "main.py"]
