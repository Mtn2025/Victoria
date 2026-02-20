# Builder stage
FROM python:3.10-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime libs for audio
RUN apt-get update && apt-get install -y \
    libportaudio2 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy app code
COPY backend/ ./backend/
COPY config/ ./config/

# Env vars
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Production command (no reload, multiple workers)
CMD ["uvicorn", "backend.interfaces.http.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
