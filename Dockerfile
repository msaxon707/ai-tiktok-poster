FROM python:3.11-slim

WORKDIR /app
COPY . /app

# Install dependencies and ensure ffmpeg is installed before moviepy # rebuild trigger 2025-11-10
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip
RUN pip install openai moviepy pillow python-dotenv requests

CMD ["python", "main.py"]
