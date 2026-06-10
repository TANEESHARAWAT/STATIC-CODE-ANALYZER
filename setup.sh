#!/usr/bin/env bash
set -e
echo "=== Static Code Analyzer — Setup ==="
python3 --version 2>/dev/null || { echo "[ERROR] Python 3 not found."; exit 1; }
if [ ! -d "venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null
echo "[2/3] Installing dependencies..."
pip install --upgrade pip -q
pip install antlr4-python3-runtime==4.13.1 anthropic flask -q
echo "[3/3] Done!"
echo ""
echo "To run the Web UI:"
echo "  source venv/bin/activate"
echo "  python server.py"
echo "  Open: http://localhost:5000"
echo ""
echo "To run via CLI:"
echo "  python main.py samples/bad_code.c"
echo "  python main.py samples/bad_code.c --dashboard"
