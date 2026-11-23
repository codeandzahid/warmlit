#!/usr/bin/env bash
# Warmlit local run (Linux/macOS). Web UI on http://localhost:8765
set -e
cd "$(dirname "$0")"
[ -f .env ] || cp .env.example .env
mkdir -p data/memory data/workspace
python3 apps/web/server.py
