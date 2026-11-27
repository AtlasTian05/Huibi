#!/usr/bin/env bash
# Starts only this project's already-initialised local PostgreSQL cluster.
set -euo pipefail
cd "$(dirname "$0")/.."
pg_ctl="$PWD/.runtime/postgres/bin/pg_ctl"
cluster="$PWD/data/postgres"
if [[ ! -x "$pg_ctl" || ! -f "$cluster/PG_VERSION" ]]; then
  printf 'No project-local PostgreSQL cluster; start your installed PostgreSQL service instead.\n' >&2
  exit 1
fi
port="$(.venv/bin/python - <<'PY'
import os
from dotenv import load_dotenv
load_dotenv('.env')
if os.getenv('POSTGRES_HOST', 'localhost') not in {'localhost', '127.0.0.1'}:
    raise SystemExit('Configured database is not local; refusing to start a local cluster')
port = int(os.getenv('POSTGRES_PORT', '5432'))
assert 1 <= port <= 65535
print(port)
PY
)"
if "$pg_ctl" -D "$cluster" status >/dev/null 2>&1; then
  printf 'Project PostgreSQL is already running.\n'
else
  "$pg_ctl" -D "$cluster" -l "$PWD/.runtime/postgres.log" -o "-h 127.0.0.1 -p $port" -w start
fi
