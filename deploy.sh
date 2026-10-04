#!/bin/bash
# ==============================================================================
# IBVAP (Intelligent Border Video Analytics Platform) Production Deployment Tool
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

case "$1" in
    start)
        echo "=========================================================="
        echo "  Deploying IBVAP Production Stack"
        echo "=========================================================="
        systemctl --user daemon-reload

        echo "[1/4] Starting Gunicorn Backend on 127.0.0.1:5001..."
        systemctl --user restart ibvap-backend.service

        echo "[2/4] Starting Pre-compiled React 19 SSR Node Server on 127.0.0.1:3000..."
        systemctl --user restart ibvap-frontend.service

        sleep 2

        echo "[3/4] Starting Caddy High-Speed Reverse Proxy on :5000 and :8080..."
        systemctl --user restart ibvap-caddy.service

        echo "[4/4] Starting Cloudflare Tunnel Daemon..."
        systemctl --user restart cloudflared-tunnel.service

        sleep 3
        echo "=========================================================="
        echo "  Deployment Status Verification"
        echo "=========================================================="
        systemctl --user --no-pager status ibvap-backend.service ibvap-frontend.service ibvap-caddy.service cloudflared-tunnel.service | grep -E "Loaded:|Active:"
        echo ""
        if [ -f "$DIR/TUNNEL_URL.txt" ]; then
            echo "  ✓ Public Live URL: $(cat "$DIR/TUNNEL_URL.txt")"
        fi
        echo "  ✓ Local Dashboard: http://localhost:5000 or http://localhost:8080"
        echo "  ✓ Backend API:     http://localhost:5000/api/overview"
        echo "=========================================================="
        ;;

    stop)
        echo "Stopping IBVAP services..."
        systemctl --user stop cloudflared-tunnel.service ibvap-caddy.service ibvap-frontend.service ibvap-backend.service
        echo "All IBVAP services stopped."
        ;;

    restart)
        $0 stop
        sleep 1
        $0 start
        ;;

    status)
        echo "=== IBVAP Service Status ==="
        systemctl --user --no-pager status ibvap-backend.service ibvap-frontend.service ibvap-caddy.service cloudflared-tunnel.service
        echo ""
        if [ -f "$DIR/TUNNEL_URL.txt" ]; then
            echo "Current Public URL: $(cat "$DIR/TUNNEL_URL.txt")"
        fi
        ;;

    build)
        echo "Building production frontend assets..."
        (cd "$DIR/frontend" && npm run build)
        ;;

    test)
        echo "Running full verification test suite..."
        python3 "$DIR/test_platform.py"
        ;;

    logs)
        journalctl --user -u ibvap-backend -u ibvap-frontend -u ibvap-caddy -u cloudflared-tunnel -f
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|status|build|test|logs}"
        exit 1
        ;;
esac
