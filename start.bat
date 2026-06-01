@echo off
echo.
echo  =============================================
echo   AI Creative Studio v2.0 - Full Stack
echo  =============================================
echo.
echo  Starting FastAPI Backend on http://localhost:8000
echo  Starting React Frontend on http://localhost:5173
echo.

start "AI Studio Backend" cmd /k "cd /d %~dp0backend && uvicorn main:app --reload --port 8000"
timeout /t 3 /nobreak >nul
start "AI Studio Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo  Both servers started!
echo  Backend docs: http://localhost:8000/docs
echo  Frontend app: http://localhost:5173
echo.
pause
