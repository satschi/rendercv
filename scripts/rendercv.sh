#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT_FILE="${1:-CV.yaml}"
OUTPUT_DIR="${2:-rendercv_output}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it from https://astral.sh/uv." >&2
  exit 1
fi

cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  uv venv
fi

uv pip install -r requirements.txt

.venv/bin/python scripts/rendercv_runner.py "$INPUT_FILE" --output-folder "$OUTPUT_DIR"
