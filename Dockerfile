FROM python:3.11-slim

WORKDIR /app
COPY . /app

# --- install ffmpeg before python packages ---
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip
RUN pip install --no-cache-dir openai moviepy pillow python-dotenv requests

CMD ["python", "main.py"]
# rebuild trigger Nov 11
