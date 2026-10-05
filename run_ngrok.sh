#!/bin/bash
# run_ngrok.sh - Persistent ngrok tunnel to Caddy Reverse Proxy (Port 5000)
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="$DIR/TUNNEL_URL.txt"

NGROK_BIN="$(command -v ngrok || echo "$HOME/.local/bin/ngrok")"

# Source environment variables if .env exists
if [ -f "$DIR/.env" ]; then
    set -a
    source "$DIR/.env"
    set +a
fi

killall -9 ngrok 2>/dev/null || true
sleep 1

DOMAIN="${NGROK_DOMAIN:-$1}"

if [ -n "$DOMAIN" ]; then
    echo "https://$DOMAIN" > "$OUTPUT_FILE"
    echo "Starting persistent ngrok tunnel: https://$DOMAIN -> Caddy (Port 5000)..."
    exec "$NGROK_BIN" http --url="$DOMAIN" 5000 --log=stdout
else
    echo "Starting ngrok tunnel on Caddy (Port 5000)..."
    exec "$NGROK_BIN" http 5000 --log=stdout
fi
