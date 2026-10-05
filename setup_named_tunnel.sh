#!/bin/bash
set -e

DOMAIN=$1
TUNNEL_NAME=${2:-"ibvap-surveillance"}

if [ -z "$DOMAIN" ]; then
    echo "Usage: ./setup_named_tunnel.sh <your-domain.com or cctv.yourdomain.com> [tunnel-name]"
    exit 1
fi

if [ ! -f "$HOME/.cloudflared/cert.pem" ]; then
    echo "Error: $HOME/.cloudflared/cert.pem not found!"
    echo "Please complete the Cloudflare browser authorization first via:"
    echo "cloudflared tunnel login"
    exit 1
fi

echo "==> Creating Cloudflare Named Tunnel: $TUNNEL_NAME..."
# Create tunnel or get existing ID if it already exists
TUNNEL_OUTPUT=$(cloudflared tunnel create "$TUNNEL_NAME" 2>&1 || true)
echo "$TUNNEL_OUTPUT"

TUNNEL_ID=$(echo "$TUNNEL_OUTPUT" | grep -oE "[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}" | head -n 1)

if [ -z "$TUNNEL_ID" ]; then
    # Try fetching existing tunnel ID
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
fi

if [ -z "$TUNNEL_ID" ]; then
    echo "Failed to determine Tunnel ID. Check cloudflared tunnel list."
    exit 1
fi

echo "==> Tunnel ID: $TUNNEL_ID"

echo "==> Routing DNS for hostname: $DOMAIN..."
cloudflared tunnel route dns -f "$TUNNEL_NAME" "$DOMAIN"

echo "==> Generating persistent config file at $HOME/.cloudflared/config.yml..."
cat <<EOF > "$HOME/.cloudflared/config.yml"
tunnel: $TUNNEL_ID
credentials-file: $HOME/.cloudflared/${TUNNEL_ID}.json

ingress:
  # Route all traffic through Caddy Unified Reverse Proxy
  - hostname: $DOMAIN
    service: http://127.0.0.1:8080

  # Default Fallback
  - service: http_status:404
EOF

echo "==> Enabling and starting systemd services..."
systemctl --user daemon-reload
systemctl --user enable --now ibvap-backend.service
systemctl --user enable --now ibvap-frontend.service
systemctl --user enable --now cloudflared-tunnel.service

echo "==> Deployment Complete! Persistent Public URL: https://$DOMAIN"
EOF
