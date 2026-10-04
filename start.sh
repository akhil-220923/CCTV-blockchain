#!/bin/bash
set -e

# Start production React SSR if built, otherwise fallback to dev server
if [ -f "/app/frontend/.output/server/index.mjs" ]; then
    echo "[IBVAP System] Launching Production React 19 Command Center on port 3000..."
    (PORT=3000 HOST=0.0.0.0 node /app/frontend/.output/server/index.mjs) &
elif [ -d "/app/frontend" ]; then
    echo "[IBVAP System] Launching Frontend Command Center on port 3000..."
    (cd /app/frontend && npm run dev -- --host 0.0.0.0 --port 3000) &
fi

# Wait for frontend server to bind port
sleep 2

# Start Python WSGI Server with multi-threading
echo "[IBVAP System] Launching Gunicorn WSGI Backend on port ${PORT:-5000}..."
if command -v gunicorn >/dev/null 2>&1; then
    exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 12 --timeout 120 web.server:app
else
    exec python3 web/server.py
fi
