@echo off
REM Warmlit local run (Windows). Web UI on http://localhost:8765
cd /d %~dp0
if not exist .env copy .env.example .env
if not exist data\memory mkdir data\memory
if not exist data\workspace mkdir data\workspace
python apps\web\server.py
pause
