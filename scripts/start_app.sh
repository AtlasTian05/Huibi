#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f frontend/dist/index.html ]]; then
  printf 'Build the frontend first: cd frontend && npm ci && npm run build\n' >&2
  exit 1
fi
if [[ -x .runtime/postgres/bin/pg_ctl && -f data/postgres/PG_VERSION ]]; then
  ./scripts/start_db.sh
fi
exec .venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000
