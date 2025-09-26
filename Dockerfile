FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# Dependencias mínimas para opencv-python (wheels) y mediapipe
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY proyecto_0/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["python", "main.py"]
