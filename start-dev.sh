#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$ROOT/.venv/Scripts/python.exe"
if [[ ! -f "$PY" ]]; then
  PY="python"
fi

echo "Starting PlanetMind control-plane, backend, and frontend..."

cd "$ROOT/control-plane"
"$PY" manage.py migrate
"$PY" manage.py runserver 0.0.0.0:8100 &
CONTROL_PID=$!

cd "$ROOT/backend"
export CONTROL_PLANE_BASE_URL="http://localhost:8100"
export CONTROL_PLANE_ENFORCE_GOVERNANCE="true"
export CONTROL_PLANE_SYNC_ENABLED="true"
PYTHONPATH=. "$PY" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd "$ROOT/frontend"
if [[ ! -d node_modules ]]; then
  npm install
fi
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

echo ""
echo "Control Plane: http://localhost:8100"
echo "Backend:       http://localhost:8000"
echo "Frontend:      http://localhost:5173"
echo ""
echo "First run only: seed the control-plane org/admin from another terminal:"
echo "  cd control-plane && python manage.py bootstrap_control_plane --org-name \"PlanetMind Org\" --org-slug planetmind-org --admin-username orgadmin --admin-email orgadmin@example.com --admin-password \"ChangeThisPassword123!\""
echo ""
echo "Press Ctrl+C to stop all services."

trap 'kill $CONTROL_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' INT TERM
wait
