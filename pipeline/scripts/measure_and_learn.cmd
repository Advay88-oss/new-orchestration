@echo off
REM Measure -> Learn, run on a schedule independent of Claude.
REM Pulls live engagement for published posts (needs the OpenCLI bridge up; degrades
REM gracefully to competitor-only learning if it is down), then re-derives INSIGHTS.
setlocal
set PYTHONIOENCODING=utf-8
set "PATH=%PATH%;%APPDATA%\npm"
cd /d "D:\new orchestration"
set "PY=C:\Users\Advay Anand\.agent-reach-venv\Scripts\python.exe"
echo. >> pipeline\logs\learning.log
echo [%date% %time%] === measure + learn === >> pipeline\logs\learning.log
"%PY%" pipeline\scripts\performance_tracker.py >> pipeline\logs\learning.log 2>&1
"%PY%" pipeline\scripts\learn.py >> pipeline\logs\learning.log 2>&1
endlocal
