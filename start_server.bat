@echo off
title scheduleSYS Backend
cd /d "%~dp0backend"
echo Starting scheduleSYS on http://localhost:8080 ...
echo Open browser: http://localhost:8080
echo Login: 990101000001 / admin123
echo Press Ctrl+C to stop
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
pause
