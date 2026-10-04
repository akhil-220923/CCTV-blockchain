FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies (OpenCV, FFmpeg, curl, gnupg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 22 LTS for the frontend command center
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and install CPU-optimized PyTorch
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision

# Copy backend requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend manifests and install node packages
COPY frontend/package.json frontend/package-lock.json* ./frontend/
RUN cd frontend && npm install

# Copy entire application
COPY . .

# Ensure start script is executable
RUN chmod +x /app/start.sh

# Expose backend (5000) and frontend (3000)
EXPOSE 5000 3000

ENV PORT=5000 \
    HOST=0.0.0.0 \
    FRONTEND_URL=http://localhost:3000 \
    VITE_BACKEND_URL=http://localhost:5000

CMD ["/app/start.sh"]
