# CCTV-Blockchain — Intelligent Border Video Analytics Platform (IBVAP)

[![Deployment Status](https://img.shields.io/badge/deployment-live%20HTTPS-brightgreen.svg)](#production-deployment)
[![Consensus Mesh](https://img.shields.io/badge/blockchain-3--node%20PoA%20mesh-blue.svg)](#blockchain-setup)
[![AI Engine](https://img.shields.io/badge/AI%20Inference-YOLOv8--LLVIP-orange.svg)](#ai-model-setup)
[![Security Standard](https://img.shields.io/badge/cryptography-Ed25519%20%2B%20SHA--256-purple.svg)](#security-notes)

---

## 1. Project Overview

The **Intelligent Border Video Analytics Platform (IBVAP)** is a decentralized, forensic-grade perimeter defense and surveillance system. It integrates computer vision (YOLOv8 & ByteTrack) with a 3-node inter-agency blockchain mesh (Border Police, State Police, and Judiciary) to guarantee tamper-proof chain of custody for perimeter intrusion events.

Every camera frame capturing an intrusion is cryptographically hashed with SHA-256 and digitally signed using hardware-isolated Ed25519 keys directly at ingestion. Intrusion events are anchored across all three authority ledgers simultaneously, making evidence alteration, breach concealment, and unauthorized tampering instantly detectable by cryptographic consensus.

---

## 2. System Architecture

```
                                [ Any Device: Phone / Tablet / Laptop / Desktop ]
                                                         │
                                                         ▼
                                            [ Cloudflare Edge HTTPS ]
                                                         │
                                                         ▼ Cloudflare Tunnel
                                            ┌─────────────────────────┐
                                            │   Caddy Reverse Proxy   │
                                            │   (Ports :5000 & :8080) │
                                            └────────────┬────────────┘
                                                         │
                         ┌───────────────────────────────┴───────────────────────────────┐
                         │                                                               │
     Static Assets & SSR (/ & /assets/*)                                REST API, Streams & Evidence (/api, /video, /evidence)
                         │                                                               │
                         ▼ Port 3000                                                     ▼ Port 5001 (WSG / Gunicorn)
              ┌─────────────────────┐                                         ┌─────────────────────┐
              │   React 19 / Vite   │                                         │    Flask Backend    │
              │   Command Center    │                                         │   (Gunicorn WSGI)   │
              └─────────────────────┘                                         └──────────┬──────────┘
                                                                                         │
                                                    ┌────────────────────────────────────┼────────────────────────────────────┐
                                                    │                                    │                                    │
                                                    ▼                                    ▼                                    ▼
                                         ┌─────────────────────┐              ┌─────────────────────┐              ┌─────────────────────┐
                                         │     AI Pipeline     │              │ 3-Node Blockchain   │              │   Forensic Vault    │
                                         │  (YOLOv8 + ByteTrack│              │  (Border, State,    │              │  (Ed25519 Signatures│
                                         │   + Zone Manager)   │              │     Judiciary)      │              │   + SHA-256 Hashing)│
                                         └─────────────────────┘              └─────────────────────┘              └─────────────────────┘
```

---

## 3. Key Features

- **Decentralized 3-Node Architecture:** Full-mesh P2P consensus replication across Border Police (tactical operations), State Police (regional law enforcement), and Judiciary (forensic scrutiny and court evidence sealing).
- **Certified AI Vision Pipeline:** Custom LLVIP border surveillance YOLOv8 neural network with ByteTrack multi-object tracking and restricted polygon zone intrusion analysis.
- **Anti-Spam Dwell De-duplication:** Tracks intruders over continuous dwell frames and triggers exactly one cryptographically sealed intrusion event per entry, eliminating log floods.
- **PKI Personnel Authorization:** Cryptographic access control with role-based exemption for authorized border patrol personnel, preventing false alarms.
- **Inter-Agency Audit Notification:** Any access or inspection of audit ledgers by one stakeholder is automatically broadcast and cryptographically recorded across peer nodes.
- **Forensic Tamper Detection:** Bit-level tamper detection on evidence snapshots and consensus-based detection of status alteration (e.g. attempting to conceal a breach by changing `INTRUSION_DETECTED` to `NO_INTRUSION_DETECTED`).
- **Universal Multi-Device Access:** Cross-browser, responsive interface engineered for desktop, tablet, and mobile devices (iOS / Android) over a single public HTTPS URL.
- **Direct Video & Image Uploads:** Live testing and analysis of uploaded surveillance videos and single-frame snapshots via dedicated API endpoints and frontend controls.

---

## 4. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend HUD** | React 19, TanStack Start, TanStack Router, Vite 8, Tailwind CSS v4, Lucide Icons, Radix UI |
| **Backend API** | Python 3.11, Flask, Gunicorn WSGI (multi-threaded), OpenCV, NumPy |
| **AI Inference** | Ultralytics YOLOv8, PyTorch (CPU fallback + CUDA GPU acceleration), ByteTrack |
| **Cryptography** | Ed25519 digital signatures (`cryptography`), SHA-256 hashing, Merkle Trees |
| **Reverse Proxy** | Caddy v2, Nginx |
| **Public Ingress** | Cloudflare Tunnel (HTTPS with zero exposed router ports) |
| **Containers** | Docker, Docker Compose |

---

## 5. Folder Structure

```
CCTV-blockchain/
├── ai_pipeline/                  # AI detection, ByteTrack tracking & zone analysis
│   ├── detector.py               # BorderPersonDetector (YOLOv8 + hash verification)
│   ├── tracker.py                # ByteTracker multi-object tracking
│   ├── video_processor.py        # End-to-end surveillance video processor
│   ├── zone_manager.py           # Polygon perimeter zone & personnel exemption
│   ├── epoch_02.pt.part_*        # Certified model checkpoint split parts (<100MB)
│   └── output/                   # Processed & annotated surveillance videos
├── backend/                      # Hyperledger Fabric reference & client tools
├── blockchain/                   # 3-Node decentralized blockchain network
│   ├── block.py                  # Cryptographic Block data structure & Merkle root
│   ├── crypto_utils.py           # Ed25519 signing, verification & SHA-256 hashing
│   ├── ledger.py                 # BlockchainLedger (cameras, models, audit logs)
│   └── node.py                   # 3-node inter-agency node network & consensus sync
├── blockchain_data/              # Persistent on-disk ledgers for each authority node
│   ├── BorderPolice-Node/        # Border Police ledger.json & audit_log.json
│   ├── StatePolice-Node/         # State Police ledger.json & audit_log.json
│   └── Judiciary-Node/           # Judiciary ledger.json & audit_log.json
├── evidence/                     # Cryptographically signed JPEG intrusion frames
├── frontend/                     # Modern React 19 / TanStack Start Command Center
│   ├── src/routes/index.tsx      # Unified Command Center HUD & tabs
│   ├── package.json              # Node dependencies
│   └── vite.config.ts            # Vite & Nitro SSR configuration
├── scripts/                      # Cross-platform automation scripts
│   ├── setup.sh                  # Automated environment setup (Linux/WSL)
│   ├── start.sh                  # Launch all production services
│   ├── stop.sh                   # Stop all production services
│   ├── healthcheck.sh            # End-to-end health verification
│   ├── setup.ps1                 # Windows PowerShell setup
│   └── start.ps1                 # Windows PowerShell startup
├── security/                     # Ed25519 camera keypairs & verification scripts
├── video/                        # Input CCTV video streams & uploads
├── web/                          # Production Flask API server
│   └── server.py                 # REST API, video streaming, upload & proxy handlers
├── Caddyfile                     # Production high-speed reverse proxy configuration
├── cloudflared-config.yml        # Cloudflare Named Tunnel configuration
├── deploy.sh                     # Unified management CLI (start|stop|restart|test|build)
├── docker-compose.yml            # Local development Docker Compose stack
├── docker-compose.prod.yml       # Hardened production Docker Compose stack
├── Dockerfile                    # Multi-stage all-in-one container
├── Dockerfile.backend            # Dedicated Python AI/blockchain backend container
├── requirements.txt              # Python dependencies
└── test_platform.py              # Full 9-stage end-to-end verification test suite
```

---

## 6. Requirements

### Hardware:
- **CPU:** Dual-core 2.0 GHz or higher (x86_64 or ARM64)
- **RAM:** Minimum 2 GB (4 GB+ recommended for YOLOv8 inference)
- **Disk:** 5 GB free disk space
- **GPU (Optional):** NVIDIA GPU with CUDA support (falls back to CPU automatically)

### Software:
- **Python:** 3.10, 3.11, or 3.12
- **Node.js:** 20+ or 22 LTS with `npm`
- **Docker & Docker Compose** (for containerized deployments)
- **Caddy** (v2+) or **Nginx**
- **cloudflared** (for Cloudflare Tunnel ingress)

---

## 7. Local Development

### Option A: Bare-Metal / WSL2 Local Run

1. **Clone the repository:**
   ```bash
   git clone https://github.com/akhil-220923/CCTV-blockchain.git
   cd CCTV-blockchain
   ```

2. **Run automated setup:**
   ```bash
   ./scripts/setup.sh
   ```

3. **Start services:**
   ```bash
   # Terminal 1: Start Backend API (Port 5000)
   python3 web/server.py

   # Terminal 2: Start Frontend Dev Server (Port 3000)
   cd frontend && npm run dev -- --host 0.0.0.0 --port 3000
   ```

4. **Access the HUD:**
   Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 8. Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

| Variable | Default | Purpose |
|---|---|---|
| `NODE_ENV` | `production` | Node execution environment |
| `PORT` | `5000` | Backend API listen port |
| `HOST` | `0.0.0.0` | Backend host bind address |
| `FRONTEND_URL` | `http://frontend:3000` | Frontend SSR target URL |
| `VITE_BACKEND_URL` | `http://backend:5000` | Backend URL for Vite SSR proxy |
| `CORS_ORIGIN` | `*` | Allowed CORS origins |
| `MODEL_PATH` | `ai_pipeline/epoch_02.pt` | Certified YOLOv8 model path |
| `FALLBACK_MODEL` | `yolov8s.pt` | Secondary model for fallback |
| `BLOCKCHAIN_DATA_PATH` | `blockchain_data` | Persistent blockchain directory |
| `EVIDENCE_PATH` | `evidence` | Intrusion evidence images directory |
| `DOMAIN_NAME` | `yourdomain.com` | Production public domain |

---

## 9. Docker Deployment

### Local Development Stack
```bash
docker compose up --build
```
Access points:
- Unified Proxy: [http://localhost](http://localhost) (Port 80)
- Backend: [http://localhost:5000](http://localhost:5000)
- Frontend: [http://localhost:3000](http://localhost:3000)

### Production Hardened Stack (Internal Ports Protected)
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
In this mode, only the reverse proxy (Port 80) is accessible externally. All internal service communication occurs over the isolated Docker network `ibvap-network`.

---

## 10. Cloudflare Deployment (Stable Public HTTPS)

### Quick Tunnel (Zero-configuration public URL)
```bash
./deploy.sh start
cat TUNNEL_URL.txt
```
This generates a live public HTTPS URL accessible from any mobile phone, tablet, or external computer:
```
https://<random-id>.trycloudflare.com
```

### Named Tunnel (Custom Domain)
1. Authenticate with your Cloudflare account:
   ```bash
   cloudflared tunnel login
   ```
2. Configure tunnel for your domain:
   ```bash
   ./setup_named_tunnel.sh your-domain.com
   ```
3. Your platform will be accessible at:
   ```
   https://your-domain.com/
   ```

---

## 11. Production Deployment via `./deploy.sh`

The unified deployment tool manages all background systemd daemons:

```bash
# Start all production services (Backend, Frontend SSR, Caddy, Cloudflare)
./deploy.sh start

# Check service health & view active public HTTPS URL
./deploy.sh status

# Stream unified multi-service logs
./deploy.sh logs

# Stop all services
./deploy.sh stop

# Restart services
./deploy.sh restart
```

---

## 12. API Documentation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check (backend, timestamp, node IDs) |
| `GET` | `/api/health` | API health check for reverse proxies and monitors |
| `GET` | `/api/overview` | Platform metrics, camera status, model hash, intrusion counts |
| `GET` | `/api/nodes` | Consensus status of Border Police, State Police, Judiciary |
| `GET` | `/api/blockchain/chain` | Full block explorer for requested node (`?node=border_police`) |
| `GET` | `/api/events` | Recorded perimeter intrusion events with tamper evaluations |
| `GET` | `/api/audit-logs` | Immutable audit log records for requested authority node |
| `POST`| `/api/audit-logs/access` | Log and broadcast cross-agency audit access notice |
| `GET` | `/api/personnel` | Roster of authorized PKI exempt personnel |
| `POST`| `/api/personnel/authorize` | Grant/toggle clearance for personnel ID or track ID |
| `GET` | `/api/verify/evidence/<id>` | Forensic judicial verification of evidence snapshot |
| `POST`| `/api/intrusion/change-status` | Alter intrusion status to simulate concealment tampering |
| `POST`| `/api/simulate/tamper-evidence` | Simulate disk bit-flip alteration on evidence frame |
| `POST`| `/api/simulate/restore` | Restore consensus state across all 3 authority nodes |
| `POST`| `/api/process-video` | Trigger complete AI analysis on active CCTV video |
| `POST`| `/api/upload/video` | Upload custom surveillance video (`.mp4`, `.avi`, `.mov`) |
| `POST`| `/api/upload/image` | Upload snapshot for instant YOLOv8 person detection |
| `GET` | `/video/stream/annotated` | Live low-latency MJPEG video stream with bounding boxes |
| `GET` | `/video/stream/raw` | Live low-latency raw CCTV video stream |
| `GET` | `/video/annotated` | Download H.264 MP4 annotated surveillance recording |
| `GET` | `/evidence/<filename>` | Retrieve cryptographically signed intrusion snapshot |

---

## 13. AI Model Setup

The platform uses the certified **LLVIP Border Surveillance YOLOv8 checkpoint** (`ai_pipeline/epoch_02.pt`) for high-accuracy nocturnal and thermal person detection, with automatic fallback to `yolov8s.pt` / `yolov8n.pt`.

### Automated Model Part Reassembly:
To adhere to GitHub's 100 MB per-file limit, the 109 MB certified model weights are tracked as split parts:
- `ai_pipeline/epoch_02.pt.part_aa` (60 MB)
- `ai_pipeline/epoch_02.pt.part_ab` (49 MB)

The model is automatically assembled on startup by:
1. `scripts/setup.sh` or `scripts/setup.ps1`
2. `detector.py`'s automatic self-assembly mechanism on first initialization.

To manually reassemble the model:
```bash
cat ai_pipeline/epoch_02.pt.part_* > ai_pipeline/epoch_02.pt
```

Computed cryptographic model hash (SHA-256):
```
b333639bc8d8343bb61ae10fa58311515b8f0f3545b580d0ff0ccc31464e9bef
```

---

## 14. Blockchain Setup

The 3-node network is initialized in full-mesh topology across:
1. **Border Police Node (`BorderPolice-Node`):** Port 8001 — Ingests live CCTV, verifies camera Ed25519 signatures, registers cameras and personnel.
2. **State Police Node (`StatePolice-Node`):** Port 8002 — Replicates state, monitors cross-jurisdiction alerts, logs audit accesses.
3. **Judiciary Node (`Judiciary-Node`):** Port 8003 — Scrutinizes evidence integrity, anchors certified model hashes, rules on evidence admissibility.

Consensus blocks include:
- `previous_hash` (SHA-256)
- `merkle_root` (Merkle tree computed over all block transactions)
- `timestamp`
- `validator_node`
- `transactions` (Camera registrations, model certifications, intrusion evidence, personnel authorizations)

Ledgers persist continuously in:
```
blockchain_data/
├── BorderPolice-Node/ledger.json
├── StatePolice-Node/ledger.json
└── Judiciary-Node/ledger.json
```

---

## 15. Evidence Storage & Chain of Custody

When an intrusion is detected:
1. The exact video frame is captured at native resolution.
2. The frame's SHA-256 hash is computed.
3. The camera signs the frame hash using its private Ed25519 key.
4. The transaction is anchored into the blockchain ledger.
5. The JPEG snapshot is stored in `evidence/`.

Evidence filenames follow standard naming:
```
evidence/intrusion_<CAMERA_ID>_track_<TRACK_ID>_frame_<FRAME_NUM>.jpg
```

---

## 16. Verification & Testing

Run the full end-to-end test suite:
```bash
python3 test_platform.py
```

Tests performed:
- **Test 1:** Camera Ed25519 Key Generation & Signature Verification
- **Test 2:** Certified AI Model Hashing & Blockchain Anchoring
- **Test 3:** 3-Node Stakeholder Network Consensus & Interconnection
- **Test 4:** Person Detection & ByteTrack Multi-Object Tracking
- **Test 5:** Restricted Zone Intrusion & Anti-Spam Dwell De-duplication
- **Test 6:** PKI Cybersecurity Authorized Personnel Exemption
- **Test 7:** Cross-Node Audit Access Logging & Inter-Agency Notification
- **Test 8:** Cross-Node Tamper Detection (Unauthorized Modification)
- **Test 9:** Judiciary Forensic Evidence Scrutiny (Authentic vs Bit-Flipped)

---

## 17. Troubleshooting

- **Video stream appears delayed or buffering:**
  Ensure proxy buffering is disabled. In `Caddyfile`, `flush_interval -1` is configured. In `nginx.conf`, `proxy_buffering off;` is active for `/video/*`.
- **Port 5000 or 3000 already in use:**
  Run `./deploy.sh stop` to stop any lingering background services.
- **Model not found error:**
  Run `./scripts/setup.sh` to assemble `epoch_02.pt` from its split parts.
- **Health check failure:**
  Run `./scripts/healthcheck.sh` to inspect individual subsystem responsiveness.

---

## 18. Backup and Restore

### Create Backup:
```bash
tar -czvf ibvap_backup_$(date +%F).tar.gz blockchain_data/ evidence/ security/
```

### Restore Backup:
```bash
tar -xzvf ibvap_backup_YYYY-MM-DD.tar.gz
./deploy.sh restart
```

---

## 19. Security Notes

- **Zero Inbound Port Forwarding:** Public access is managed entirely via outbound Cloudflare Tunnels; router port forwarding is not required.
- **Internal Port Isolation:** Backend (5000/5001) and Frontend (3000) ports are bound to loopback `127.0.0.1` and isolated behind Caddy reverse proxy.
- **Ed25519 Cryptography:** High-speed elliptic-curve signatures provide tamper-proof provenance for camera hardware.
- **File Upload Protection:** Strict extension whitelisting, filename sanitization with `secure_filename`, and a 100 MB max payload limit protect against malicious uploads.
