@echo off
REM Free local AI brain for Warmlit - NO API key, ever.
REM 1) Install Ollama from https://ollama.com/download (Windows)
REM 2) This script pulls a small model (~1 GB). Warmlit auto-detects it.
where ollama >nul 2>nul
if errorlevel 1 (
  echo Ollama not found. Install it first from https://ollama.com/download
  pause
  exit /b 1
)
ollama pull qwen2.5:1.5b
echo Done. Start Warmlit with run.bat - it will use the local model alone.
pause
