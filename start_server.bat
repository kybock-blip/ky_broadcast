@echo off
chcp 65001 > nul
cd /d "%~dp0"
set "PY_CMD=python"
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
echo [건영1차아파트 안내방송시스템] 패키지 확인 중...
"%PY_CMD%" -m pip install -q -r requirements-local.txt
echo.
echo [건영1차아파트 안내방송시스템] 서버 시작: http://localhost:8100  (종료하려면 이 창을 닫거나 Ctrl+C)
echo.
rem 서버가 뜰 시간을 3초 준 뒤 브라우저를 연다
start "" /min cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:8100"
"%PY_CMD%" -m uvicorn app:app --port 8100
pause
