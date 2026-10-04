#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== IBVAP System Health Check ==="
echo ""

# 1. Local backend health
echo "[1] Testing Backend Local Health (/health)..."
if curl -s -f http://127.0.0.1:5000/health >/dev/null 2>&1; then
    echo "  ✓ Local Backend /health: OK"
    curl -s http://127.0.0.1:5000/health
    echo ""
else
    echo "  ✗ Local Backend /health: FAILED"
fi

# 2. Local nodes status
echo "[2] Testing 3-Node Blockchain Consensus (/api/nodes)..."
if curl -s -f http://127.0.0.1:5000/api/nodes >/dev/null 2>&1; then
    echo "  ✓ 3-Node Network Consensus: REACHABLE"
else
    echo "  ✗ 3-Node Network Consensus: FAILED"
fi

# 3. Public Cloudflare Tunnel URL
if [ -f "$DIR/TUNNEL_URL.txt" ]; then
    PUBLIC_URL="$(cat "$DIR/TUNNEL_URL.txt")"
    echo ""
    echo "[3] Testing Public Cloudflare HTTPS Endpoint ($PUBLIC_URL)..."
    if curl -s -f "$PUBLIC_URL/health" >/dev/null 2>&1; then
        echo "  ✓ Public HTTPS /health: OK"
        curl -s "$PUBLIC_URL/health"
        echo ""
    else
        echo "  ✗ Public HTTPS /health: Not reachable or tunnel initializing"
    fi
fi

echo ""
echo "=== Health Check Complete ==="
