#!/bin/bash
# ============================================================
#  Placement Portal — One-Click Start Script
#  Run this EVERY TIME you want to start the server
# ============================================================
set -e

echo ""
echo "=========================================="
echo "  University Placement Portal v2"
echo "=========================================="
echo ""

# 1. Go to project directory
cd "$(dirname "$0")"

# 2. Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python3 not found. Install Python 3.10+"
    exit 1
fi

# 3. Install dependencies if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
fi

# 4. Clear Python cache (prevents stale route issues)
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
echo "✅ Cache cleared"

# 5. Set environment (change SECRET keys in production)
export SECRET_KEY="placement_portal_secret_change_in_prod"
export STAFF_SECRET_KEY="STAFF@2024"
export OFFICER_SECRET_KEY="OFFICER@2024"
export ADMIN_SECRET_KEY="ADMIN@SUPER2024"
export COMPANY_SECRET_KEY="COMPANY@2024"

# 6. Start server
echo ""
echo "🚀 Starting server at http://127.0.0.1:8000"
echo "   Press Ctrl+C to stop"
echo ""
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
