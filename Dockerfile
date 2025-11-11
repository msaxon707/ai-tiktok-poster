FROM python:3.11-slim

WORKDIR /app
COPY . /app

# Install system packages (needed for moviepy/ffmpeg)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir moviepy==1.0.3 pillow openai requests python-dotenv

CMD ["python", "main.py"]