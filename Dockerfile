FROM python:3.11

WORKDIR /app
COPY . /app

# Install ffmpeg and other dependencies required by moviepy
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
