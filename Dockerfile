FROM python:3.11-slim

WORKDIR /app
COPY . /app

# Install system dependencies including ffmpeg for moviepy
RUN apt-get update && apt-get install -y ffmpeg build-essential && rm -rf /var/lib/apt/lists/*

# Force reinstall all packages — avoids silent cache skips
RUN pip install --upgrade pip setuptools wheel
RUN pip install --force-reinstall --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
