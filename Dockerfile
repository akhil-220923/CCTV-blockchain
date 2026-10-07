# Stage 1: Build modern React 19 / TanStack Start production SSR bundle
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Runtime + Caddy Reverse Proxy
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies (OpenCV headless runtime, FFmpeg, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install official standalone Caddy binary (multi-arch, zero setcap/xattr restrictions)
RUN ARCH=$(dpkg --print-architecture) \
    && curl -fsSL "https://github.com/caddyserver/caddy/releases/download/v2.8.4/caddy_2.8.4_linux_${ARCH}.tar.gz" \
    | tar -xz -C /usr/local/bin caddy \
    && chmod 755 /usr/local/bin/caddy \
    && /usr/local/bin/caddy version

# Install Node.js 22 LTS runtime to execute SSR server
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and install CPU-optimized PyTorch
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision

# Copy backend requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Copy application source code
COPY . .

# Copy pre-compiled frontend production build from Stage 1
COPY --from=frontend-builder /app/frontend/.output /app/frontend/.output

# Reassemble split model weights
RUN if [ ! -f "ai_pipeline/epoch_02.pt" ] && [ -f "ai_pipeline/epoch_02.pt.part_aa" ]; then \
        echo "Reassembling certified model weights..." && \
        cat ai_pipeline/epoch_02.pt.part_* > ai_pipeline/epoch_02.pt; \
    fi

# Ensure start script is executable
RUN chmod +x /app/start.sh

# Environment defaults
ENV PORT=8080 \
    HOST=0.0.0.0

EXPOSE 8080 5000 3000

# Health check verifies that Caddy and backend respond on $PORT
HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-8080}/health || exit 1

CMD ["/app/start.sh"]
