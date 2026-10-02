#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v uv >/dev/null; then
  echo 'Install uv from https://docs.astral.sh/uv/getting-started/installation/ first.' >&2
  exit 1
fi
if [[ "${1:-cpu}" == "gpu" ]]; then
  uv sync --frozen --python 3.11 --extra inference
else
  uv sync --frozen --python 3.11
fi
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m auditbench build-cases
.venv/bin/python -m auditbench verify-data
