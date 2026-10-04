# IBVAP Complete Production Deployment Guide

This document provides exact, step-by-step instructions to deploy, verify, maintain, and recover the **Intelligent Border Video Analytics Platform (IBVAP)** on any device, cloud server (AWS EC2, DigitalOcean, Hetzner, Linode), WSL2, or Linux host.

---

## Table of Contents
- [A. Clone Repository](#a-clone-repository)
- [B. Install Prerequisites](#b-install-prerequisites)
- [C. Configure .env](#c-configure-env)
- [D. Build Containers](#d-build-containers)
- [E. Start Application](#e-start-application)
- [F. Configure Cloudflare](#f-configure-cloudflare)
- [G. Configure Domain](#g-configure-domain)
- [H. Start Cloudflare Tunnel](#h-start-cloudflare-tunnel)
- [I. Verify HTTPS](#i-verify-https)
- [J. Test API](#j-test-api)
- [K. Test AI](#k-test-ai)
- [L. Test Blockchain](#l-test-blockchain)
- [M. Test Evidence](#m-test-evidence)
- [N. Backup Data](#n-backup-data)
- [O. Restore Data](#o-restore-data)
- [P. Update Deployment](#p-update-deployment)
- [Q. Rollback Deployment](#q-rollback-deployment)

---

### A. Clone Repository

```bash
git clone https://github.com/akhil-220923/CCTV-blockchain.git
cd CCTV-blockchain
```

---

### B. Install Prerequisites

#### Debian / Ubuntu / WSL2:
```bash
sudo apt update && sudo apt install -y curl git python3 python3-pip ffmpeg libgl1 libglib2.0-0
# Install Node.js 22 LTS
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# Install cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb && rm cloudflared.deb

# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLF 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLF 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy
```

#### Run automated setup to reassemble model checkpoints and build frontend:
```bash
./scripts/setup.sh
```

---

### C. Configure .env

Create the production environment file from template:
```bash
cp .env.example .env
```
Edit `.env` to configure your domain and optional settings:
```bash
nano .env
```

---

### D. Build Containers

If deploying with Docker Compose:
```bash
# Build the production stack without running
docker compose -f docker-compose.prod.yml build
```

---

### E. Start Application

#### Method 1: Bare-Metal / WSL2 (Using `deploy.sh`)
```bash
./deploy.sh start
```
Verify status:
```bash
./deploy.sh status
```

#### Method 2: Docker Compose (Production Hardened Stack)
```bash
docker compose -f docker-compose.prod.yml up -d
```
Verify container health:
```bash
docker compose -f docker-compose.prod.yml ps
```

---

### F. Configure Cloudflare

If using a custom domain on Cloudflare:
```bash
# Authenticate cloudflared with your Cloudflare account
cloudflared tunnel login
```

---

### G. Configure Domain

Create a named tunnel and route DNS to your domain:
```bash
./setup_named_tunnel.sh your-domain.com
```

---

### H. Start Cloudflare Tunnel

#### Quick Tunnel (No domain needed):
```bash
# Starts tunnel daemon in the background and writes public HTTPS URL to TUNNEL_URL.txt
./deploy.sh start
cat TUNNEL_URL.txt
```

#### Named Tunnel:
```bash
systemctl --user enable --now cloudflared-tunnel.service
```

---

### I. Verify HTTPS

Check that the public HTTPS URL returns HTTP 200:
```bash
PUBLIC_URL=$(cat TUNNEL_URL.txt)
curl -sI "$PUBLIC_URL" | head -n 5
```
Expected output:
```
HTTP/2 200
server: cloudflare
...
```

---

### J. Test API

Run the automated healthcheck:
```bash
./scripts/healthcheck.sh
```
Or manually query the endpoints:
```bash
curl -s https://YOUR-DOMAIN/health
curl -s https://YOUR-DOMAIN/api/overview
curl -s https://YOUR-DOMAIN/api/nodes
```

---

### K. Test AI

Test image detection and model inference:
```bash
curl -s -F "file=@debug_pedestrians_crop.jpg" https://YOUR-DOMAIN/api/upload/image
```
Verify that detected bounding boxes, classes, and person counts are returned in JSON.

---

### L. Test Blockchain

Check ledger height and consensus state:
```bash
curl -s https://YOUR-DOMAIN/api/blockchain/chain?node=border_police | jq '.chain_length, .is_integrity_valid'
```
Simulate intrusion status concealment tampering:
```bash
curl -s -X POST https://YOUR-DOMAIN/api/simulate/tamper-intrusion \
  -H "Content-Type: application/json" \
  -d '{"event_id":"INTRUSION-DET-001","node":"state_police","status":"NO_INTRUSION_DETECTED"}'
```
Notice peer nodes immediately detect the disparity. Restore consensus:
```bash
curl -s -X POST https://YOUR-DOMAIN/api/simulate/restore
```

---

### M. Test Evidence

Verify evidence frame forensics with Judiciary node:
```bash
curl -s https://YOUR-DOMAIN/api/verify/evidence/INTRUSION-DET-001 | jq '.is_authentic_forensic_evidence, .hash_matches, .signature_valid'
```
Expected:
```json
true
true
true
```

---

### N. Backup Data

To take a complete snapshot of all blockchain ledgers, evidence files, and cryptographic keys:
```bash
tar -czvf "ibvap_backup_$(date +%Y%m%d_%H%M%S).tar.gz" blockchain_data/ evidence/ security/
```

---

### O. Restore Data

To restore from a backup archive:
```bash
./deploy.sh stop
tar -xzvf ibvap_backup_*.tar.gz
./deploy.sh start
./scripts/healthcheck.sh
```

---

### P. Update Deployment

To pull updates and re-deploy without downtime:
```bash
git pull origin main
./scripts/setup.sh
./deploy.sh restart
```

---

### Q. Rollback Deployment

To revert to a previous git commit or restore state:
```bash
git checkout <PREVIOUS_COMMIT_SHA>
./deploy.sh restart
./scripts/healthcheck.sh
```
