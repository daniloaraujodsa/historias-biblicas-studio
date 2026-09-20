#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
PORT="${PORT:-8765}"
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload
