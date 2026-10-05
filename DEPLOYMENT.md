# IBVAP Complete Production Cloud Deployment Guide

This document provides exact, step-by-step instructions to deploy, verify, maintain, and recover the **Intelligent Border Video Analytics Platform (IBVAP)** on **Render Cloud**, Docker containers, cloud VPS (AWS, GCP, DigitalOcean, Hetzner), or standalone Linux servers.

---

## Architecture Flow (Cloud Production)

```
                      INTERNET (Mobile / Desktop / Laptop)
                                     |
                                     v
                   PERMANENT CLOUD HTTPS PUBLIC ENDPOINT
                 (e.g., https://sih-182-tracevasp.onrender.com)
                                     |
                                     v
                    CADDY REVERSE PROXY (:{\$PORT:8080})
                                     |
                 +-------------------+-------------------+
                 |                                       |
                 v                                       v
      FRONTEND COMMAND CENTER                     BACKEND REST API
     React 19 / TanStack Start SSR                    Gunicorn
            (Port 3000)                              (Port 5001)
                                                         |
                                 +-----------------------+-----------------------+
                                 |                       |                       |
                                 v                       v                       v
                             AI PIPELINE             BLOCKCHAIN               EVIDENCE
                         YOLOv8-LLVIP Inference   3-Node Consensus Mesh    Ed25519 Signed
                            ByteTrack Tracker     Border / State / Court   SHA-256 Hashed
                                 |
                                 v
                          VIDEO STREAMING
                         Real-time MJPEG /
                         Web H.264 Playback
```

---

## 1. Render Cloud Deployment (Primary — Zero PC Dependency)

Deploy directly from GitHub repository `https://github.com/akhil-220923/CCTV-blockchain`.

### Step 1: Render Configuration
1. Open [https://dashboard.render.com](https://dashboard.render.com) and sign in.
2. Select your Web Service (or click **New +** -> **Web Service**).
3. Connect repository: `https://github.com/akhil-220923/CCTV-blockchain` (Branch: `main`).
4. Configuration parameters:
   - **Name:** `sih-182-tracevasp` (or any custom service name)
   - **Environment:** `Docker`
   - **Dockerfile Path:** `Dockerfile`
   - **Docker Context:** `.`
   - **Health Check Path:** `/health`
   - **Region:** `Oregon` (or closest to your users)
   - **Plan:** `Free` (or `Starter` $7/mo for 1GB RAM and 0 cold starts)

### Step 2: Environment Variables (Render Dashboard)
Add these in the **Environment** tab:
```ini
PORT=10000
CORS_ORIGIN=*
PYTHONUNBUFFERED=1
```

### Step 3: Deploy
Click **Deploy Latest Commit**. Render will build the unified multi-stage container (compiling React 19 SSR, assembling AI weights, and starting Caddy + Gunicorn).

---

## Table of Contents
- [A. Clone Repository](#a-clone-repository)
- [B. Install Prerequisites](#b-install-prerequisites)
- [C. Configure .env](#c-configure-env)
- [D. Start Application Locally](#d-start-application-locally)
- [E. Docker Compose Deployment](#e-docker-compose-deployment)
- [F. Configure Ngrok Persistent Tunnel](#f-configure-ngrok-persistent-tunnel)
- [G. Verify Health & APIs](#g-verify-health--apis)
- [H. Test AI, Video, Blockchain & Evidence](#h-test-ai-video-blockchain--evidence)
- [I. Backup & Restore](#i-backup--restore)
- [J. Update & Rollback](#j-update--rollback)
- [K. Troubleshooting](#k-troubleshooting)

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

# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLF 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLF 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy

# Install official ngrok binary (if not installed)
curl -sSL https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz -o /tmp/ngrok.tgz
tar -xzf /tmp/ngrok.tgz -C ~/.local/bin/ && rm /tmp/ngrok.tgz
```

#### Run automated platform setup:
```bash
./scripts/setup.sh
```

---

### C. Configure .env

Create the production environment file from template:
```bash
cp .env.example .env
```
Edit `.env` to configure your settings:
```bash
# Server Environment
NODE_ENV=production
PORT=5000
HOST=0.0.0.0
CORS_ORIGIN=*

# Ngrok Configuration (Free Static Domain)
NGROK_DOMAIN=your-assigned-domain.ngrok-free.app

# AI & Blockchain Paths
MODEL_PATH=ai_pipeline/epoch_02.pt
FALLBACK_MODEL=yolov8s.pt
CONFIDENCE_THRESHOLD=0.15
BLOCKCHAIN_DATA_PATH=blockchain_data
EVIDENCE_PATH=evidence
VIDEO_PATH=video
```

---

### D. Start Application Locally

#### Using `deploy.sh`:
```bash
./deploy.sh start
```
Check status:
```bash
./deploy.sh status
```
Local URLs:
- **Caddy Reverse Proxy:** http://localhost:5000 or http://localhost:8080
- **Backend API:** http://localhost:5000/api/overview
- **Health Check:** http://localhost:5000/health

---

### E. Docker Compose Deployment

To deploy the entire production stack inside Docker containers:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
Verify container health:
```bash
docker compose -f docker-compose.prod.yml ps
```
Services inside Docker:
- `backend`: Internal port 5000 (Python 3.11, Gunicorn, PyTorch, YOLOv8)
- `frontend`: Internal port 3000 (Node 22 Alpine, React 19 SSR)
- `caddy`: Unified public reverse proxy on host port 80/8080 forwarding to frontend and backend

---

### F. Configure Ngrok Persistent Tunnel

To make the application permanently accessible from any phone, tablet, or external laptop without purchasing a domain:

1. **Sign up / Log in to ngrok:** [https://dashboard.ngrok.com](https://dashboard.ngrok.com)
2. **Retrieve your AuthToken:** [https://dashboard.ngrok.com/get-started/your-authtoken](https://dashboard.ngrok.com/get-started/your-authtoken)
3. **Save your authtoken securely on your system:**
   ```bash
   ngrok config add-authtoken <YOUR_NGROK_AUTHTOKEN>
   ```
4. **Retrieve your free assigned static dev domain:**
   Check [https://dashboard.ngrok.com/cloud-edge/domains](https://dashboard.ngrok.com/cloud-edge/domains) for your free permanent domain (e.g. `example-unique.ngrok-free.app`).
5. **Start the persistent tunnel to Caddy:**
   ```bash
   # Run directly or via script:
   ./run_ngrok.sh <YOUR_ASSIGNED_DOMAIN>.ngrok-free.app
   ```
   Or enable as an automatic background service:
   ```bash
   systemctl --user enable --now ibvap-ngrok.service
   ```

---

### G. Verify Health & APIs

Run the automated healthcheck:
```bash
./scripts/healthcheck.sh
```

Query via your public HTTPS endpoint:
```bash
curl -s https://<YOUR-NGROK-DOMAIN>/health
curl -s https://<YOUR-NGROK-DOMAIN>/api/overview
curl -s https://<YOUR-NGROK-DOMAIN>/api/nodes
```
Expected `/health` response:
```json
{
  "nodes": {
    "border_police": "BorderPolice-Node",
    "judiciary": "Judiciary-Node",
    "state_police": "StatePolice-Node"
  },
  "service": "backend",
  "status": "ok"
}
```

---

### H. Test AI, Video, Blockchain & Evidence

#### 1. Test AI Person Detection (Image Upload):
```bash
curl -s -F "file=@debug_frame_100.jpg" https://<YOUR-NGROK-DOMAIN>/api/upload/image
```

#### 2. Trigger Full Video Surveillance Scan:
```bash
curl -s -X POST https://<YOUR-NGROK-DOMAIN>/api/process-video
```

#### 3. Verify Blockchain Ledger Integrity:
```bash
curl -s "https://<YOUR-NGROK-DOMAIN>/api/blockchain/chain?node=border_police"
```

#### 4. Test Cryptographic Forensic Verification:
```bash
curl -s "https://<YOUR-NGROK-DOMAIN>/api/verify/evidence/INTRUSION-DET-001"
```

#### 5. Test Tamper Concealment Detection:
```bash
# Maliciously change intrusion status to 'NO_INTRUSION_DETECTED' on State Police node
curl -s -X POST https://<YOUR-NGROK-DOMAIN>/api/intrusion/change-status \
  -H "Content-Type: application/json" \
  -d '{"event_id":"INTRUSION-DET-001","node":"state_police","new_status":"NO_INTRUSION_DETECTED"}'

# Verify consensus immediately flags the integrity breach
curl -s https://<YOUR-NGROK-DOMAIN>/api/overview

# Restore ledger to authentic consensus state
curl -s -X POST https://<YOUR-NGROK-DOMAIN>/api/simulate/restore
```

---

### I. Backup & Restore

#### Backup:
```bash
tar -czvf "ibvap_backup_$(date +%Y%m%d_%H%M%S).tar.gz" blockchain_data/ evidence/ security/
```

#### Restore:
```bash
./deploy.sh stop
tar -xzvf ibvap_backup_*.tar.gz
./deploy.sh start
./scripts/healthcheck.sh
```

---

### J. Update & Rollback

#### Update:
```bash
git pull origin main
./scripts/setup.sh
./deploy.sh restart
```

#### Rollback:
```bash
git checkout <PREVIOUS_COMMIT_SHA>
./deploy.sh restart
./scripts/healthcheck.sh
```

---

### K. Troubleshooting

1. **`bind: permission denied` on Port 80:**
   - When running via non-root user (`systemctl --user`), Caddy listens on `:5000` and `:8080`. Ngrok binds directly to port `5000` or `8080`.
2. **Model Missing:**
   - Run `./scripts/setup.sh` to concatenate split model parts (`epoch_02.pt.part_*`) into `ai_pipeline/epoch_02.pt`.
3. **Public URL unreachable:**
   - Verify that your PC is awake and connected to the internet.
   - Run `./deploy.sh status` to ensure all 4 services (backend, frontend, caddy, ngrok) are active.
