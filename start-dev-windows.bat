@echo off
setlocal

set "ROOT=%~dp0"
set "CONTROL_PLANE_DIR=%ROOT%control-plane"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"

if exist "%ROOT%.venv\Scripts\python.exe" (
  set "PYTHON_CMD=%ROOT%.venv\Scripts\python.exe"
) else (
  where py >nul 2>nul
  if %ERRORLEVEL%==0 (
    set "PYTHON_CMD=py -3"
  ) else (
    set "PYTHON_CMD=python"
  )
)

echo Starting PlanetMind control-plane, backend, and frontend...

start "PlanetMind Control Plane" cmd /k "cd /d "%CONTROL_PLANE_DIR%" && %PYTHON_CMD% -m pip install -r requirements.txt && %PYTHON_CMD% manage.py migrate && %PYTHON_CMD% manage.py runserver 0.0.0.0:8100"
start "PlanetMind Backend" cmd /k "cd /d "%BACKEND_DIR%" && %PYTHON_CMD% -m pip install -r requirements.txt && set CONTROL_PLANE_BASE_URL=http://localhost:8100 && set CONTROL_PLANE_ENFORCE_GOVERNANCE=true && set CONTROL_PLANE_SYNC_ENABLED=true && %PYTHON_CMD% -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
start "PlanetMind Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && if not exist node_modules npm install && set VITE_API_BASE_URL=http://localhost:8000 && npm run dev -- --host 0.0.0.0 --port 5173"

echo.
echo Control Plane: http://localhost:8100
echo Backend:       http://localhost:8000
echo Frontend:      http://localhost:5173
echo.
echo First run only: bootstrap the control-plane org/admin in its terminal window with:
echo   python manage.py bootstrap_control_plane --org-name "PlanetMind Org" --org-slug planetmind-org --admin-username orgadmin --admin-email orgadmin@example.com --admin-password "ChangeThisPassword123!"
echo.
echo Close the three opened terminal windows to stop services.

endlocal