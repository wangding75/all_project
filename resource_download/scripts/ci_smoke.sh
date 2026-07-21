#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="server"

echo "=========================================="
echo "Step 1: Running smoke_health.py"
echo "=========================================="
python3 "${SCRIPT_DIR}/smoke_health.py"

echo ""
echo "=========================================="
echo "Step 2: Running e2e_fanqie.py"
echo "=========================================="
python3 "${SCRIPT_DIR}/e2e_fanqie.py"

echo ""
echo "=========================================="
echo "Step 3: Running e2e_hongguo.py"
echo "=========================================="
python3 "${SCRIPT_DIR}/e2e_hongguo.py"

echo ""
echo "=========================================="
echo "All CI smoke and E2E checks passed!"
echo "=========================================="
