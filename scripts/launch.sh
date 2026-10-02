#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
phase="${1:?Usage: launch.sh smoke|development|test RUN_DIRECTORY}"
out="${2:?Specify a run directory}"
case "$phase" in smoke|development|test) ;; *) exit 2;; esac
# Limits this process only. Configure provider-level instance shutdown separately.
: "${RUN_TIMEOUT_HOURS:?Set a positive process time limit, e.g. RUN_TIMEOUT_HOURS=2}"
[[ "$RUN_TIMEOUT_HOURS" =~ ^[1-9][0-9]*$ ]] || exit 2
uv run --frozen --extra inference python -m auditbench preflight
args=(--phase "$phase" --mode real --out "$out")
if [[ "$phase" == "test" ]]; then args+=(--freeze data/freeze.json); fi
timeout --signal=TERM --kill-after=60s "${RUN_TIMEOUT_HOURS}h" uv run --frozen --extra inference python -m auditbench run "${args[@]}"
uv run --frozen --extra inference python -m auditbench validate-run --out "$out"
