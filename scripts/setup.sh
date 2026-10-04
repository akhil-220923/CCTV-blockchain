#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "=========================================================="
echo "  IBVAP Automated Platform Setup & Dependency Preparation"
echo "=========================================================="

# 1. Ensure required persistent directories exist
echo "[1/5] Initializing persistent data directories..."
mkdir -p blockchain_data evidence video ai_pipeline/output scratch_frames security

# 2. Check and reassemble split model files if needed
echo "[2/5] Checking and preparing AI model files..."
if [ ! -f "ai_pipeline/epoch_02.pt" ] && ls ai_pipeline/epoch_02.pt.part_* 1>/dev/null 2>&1; then
    echo "  -> Reassembling certified model from split parts..."
    cat ai_pipeline/epoch_02.pt.part_* > ai_pipeline/epoch_02.pt
    echo "  ✓ ai_pipeline/epoch_02.pt reassembled successfully."
fi

if [ ! -f "yolov8x.pt" ] && ls yolov8x.pt.part_* 1>/dev/null 2>&1; then
    echo "  -> Reassembling YOLOv8x weights from split parts..."
    cat yolov8x.pt.part_* > yolov8x.pt
    echo "  ✓ yolov8x.pt reassembled successfully."
fi

# 3. Python environment & dependencies
echo "[3/5] Verifying Python dependencies..."
if command -v python3 >/dev/null 2>&1; then
    echo "  Python $(python3 --version) detected."
fi

# 4. Frontend dependencies & production build
echo "[4/5] Preparing frontend dependencies and assets..."
if [ -d "frontend" ] && command -v npm >/dev/null 2>&1; then
    if [ ! -d "frontend/node_modules" ]; then
        echo "  Installing frontend npm packages..."
        (cd frontend && npm install)
    fi
    echo "  Building optimized production frontend bundle..."
    (cd frontend && npm run build)
fi

# 5. Verification test run
echo "[5/5] Running verification test suite..."
python3 test_platform.py

echo "=========================================================="
echo "  ✓ IBVAP Setup Complete & Validated Successfully!"
echo "  Run ./deploy.sh start to launch production services."
echo "=========================================================="
