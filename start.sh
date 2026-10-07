#!/bin/bash
set -e

echo "[IBVAP System] Initializing Intelligent Border Video Analytics Platform..."

# 1. Reassemble split model weights if missing
if [ ! -f "/app/ai_pipeline/epoch_02.pt" ] && [ -f "/app/ai_pipeline/epoch_02.pt.part_aa" ]; then
    echo "[IBVAP System] Reassembling certified model weights from split parts..."
    cat /app/ai_pipeline/epoch_02.pt.part_* > /app/ai_pipeline/epoch_02.pt
    echo "[IBVAP System] Model weights reassembled successfully."
fi

# 2. Persistent storage handling (if volume mounted)
PERSISTENT_DIR="${PERSISTENT_DATA_PATH:-/app/persistent_data}"
if [ -d "$PERSISTENT_DIR" ]; then
    echo "[IBVAP System] Persistent storage detected at $PERSISTENT_DIR"
    mkdir -p "$PERSISTENT_DIR/blockchain_data" "$PERSISTENT_DIR/evidence" "$PERSISTENT_DIR/output"
    if [ ! -f "$PERSISTENT_DIR/blockchain_data/BorderPolice-Node/ledger.json" ] && [ -d "/app/blockchain_data" ]; then
        echo "[IBVAP System] Seeding initial 3-node blockchain consensus ledger into persistent storage..."
        cp -rn /app/blockchain_data/* "$PERSISTENT_DIR/blockchain_data/" 2>/dev/null || true
    fi
    export BLOCKCHAIN_DATA_PATH="$PERSISTENT_DIR/blockchain_data"
    export EVIDENCE_PATH="$PERSISTENT_DIR/evidence"
fi

# 3. Launch React 19 / TanStack Start Production SSR on internal port 3000
echo "[IBVAP System] Launching Production React 19 SSR on internal port 3000..."
if [ -f "/app/frontend/.output/server/index.mjs" ]; then
    (PORT=3000 HOST=127.0.0.1 node /app/frontend/.output/server/index.mjs) &
elif [ -f "./frontend/.output/server/index.mjs" ]; then
    (PORT=3000 HOST=127.0.0.1 node ./frontend/.output/server/index.mjs) &
else
    echo "[IBVAP System] Warning: Pre-built SSR server not found. Starting development server..."
    (cd /app/frontend && npm run dev -- --host 127.0.0.1 --port 3000) &
fi

# 4. Wait for internal React SSR server to be ready on port 3000
echo "[IBVAP System] Waiting for React SSR server to be ready on port 3000..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:3000/ >/dev/null 2>&1; then
        echo "[IBVAP System] React SSR is ready after ${i}s."
        break
    fi
    sleep 1
done

# 5. Launch Unified Python/Gunicorn Production Gateway on 0.0.0.0:$PUBLIC_PORT
PUBLIC_PORT="${PORT:-10000}"
echo "[IBVAP System] Launching Unified Production Gateway on 0.0.0.0:$PUBLIC_PORT..."
export FRONTEND_URL="http://127.0.0.1:3000"
exec gunicorn --bind "0.0.0.0:${PUBLIC_PORT}" --workers 1 --threads 12 --timeout 120 web.server:app
