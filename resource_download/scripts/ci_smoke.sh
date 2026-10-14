#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/server"
cd "${REPO_ROOT}"

echo "=========================================="
echo "Step 1: Running smoke_health.py"
echo "=========================================="
python3 "${SCRIPT_DIR}/smoke_health.py"

echo ""
echo "=========================================="
echo "Step 2: Running deterministic quality gate"
echo "=========================================="
python3 "${SCRIPT_DIR}/quality_gate.py"

echo ""
echo "=========================================="
echo "CI smoke and deterministic quality checks passed!"
echo "=========================================="
