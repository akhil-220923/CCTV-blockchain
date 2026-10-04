#!/bin/bash
# run_tunnel.sh - IBVAP Cloudflare Quick Tunnel Daemon
# Streams live tunnel output and extracts active public URL to TUNNEL_URL.txt

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="$DIR/TUNNEL_URL.txt"
rm -f "$OUTPUT_FILE"

CLOUDFLARED_BIN="$(command -v cloudflared || echo "$HOME/.local/bin/cloudflared")"

exec "$CLOUDFLARED_BIN" tunnel --url http://127.0.0.1:5000 2>&1 | while IFS= read -r line; do
    echo "$line"
    if [[ "$line" =~ (https://[a-zA-Z0-9-]+\.trycloudflare\.com) ]]; then
        echo "${BASH_REMATCH[1]}" > "$OUTPUT_FILE"
        echo "[IBVAP Deployment] Persistent Public URL established: ${BASH_REMATCH[1]}"
    fi
done
