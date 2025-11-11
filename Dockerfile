FROM python:3.11-slim

# Install ffmpeg (for MoviePy)
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

WORKDIR /app
COPY . /app
# rebuild trigger
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
