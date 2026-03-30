#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
  exec "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/nova_linux_worker_launch.py" "$@"
fi

if [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
  exec "$PROJECT_ROOT/.venv/bin/python" "$SCRIPT_DIR/nova_linux_worker_launch.py" "$@"
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$SCRIPT_DIR/nova_linux_worker_launch.py" "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$SCRIPT_DIR/nova_linux_worker_launch.py" "$@"
fi

echo "Kein Python-Interpreter gefunden. Bitte Python 3 installieren oder eine Linux-.venv anlegen." >&2
exit 1
