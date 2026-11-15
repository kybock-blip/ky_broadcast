@echo off
chcp 65001 > nul
setlocal EnableExtensions
cd /d "%~dp0"
title 건영1차아파트 안내방송시스템

rem ===================================================================
rem  Geonyoung 1st Apt. announcement system launcher
rem  - Installs Python 3.12 if missing (winget, else python.org installer)
rem  - Creates a private venv under %LOCALAPPDATA%\GeonyoungBroadcast and installs packages
rem    (outside OneDrive, so nothing heavy gets synced)
rem  - Creates a desktop shortcut on first run
rem  Test overrides: GY_PORT, GY_NO_BROWSER=1, GY_NO_SHORTCUT=1, GY_HOME
rem ===================================================================

set "PORT=8100"
if defined GY_PORT set "PORT=%GY_PORT%"
set "HOME_DIR=%LOCALAPPDATA%\GeonyoungBroadcast"
if defined GY_HOME set "HOME_DIR=%GY_HOME%"
set "VENV=%HOME_DIR%\venv"
set "VPY=%VENV%\Scripts\python.exe"
set "PYTHON_URL=https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"

echo.
echo  ================================================
echo    건영1차아파트 안내방송시스템
echo  ================================================
echo.

rem --- already running: just open the page ---
netstat -ano | findstr /r /c:":%PORT% .*LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo 이미 실행 중입니다. 방송 화면을 엽니다.
  if not defined GY_NO_BROWSER start "" http://localhost:%PORT%
  timeout /t 3 >nul
  exit /b 0
)

rem --- 1. find or install Python 3.12 ---
call :find_python
if defined PYEXE goto have_python
echo [1/3] Python 3.12이 없어 자동으로 설치합니다. 1~3분 걸립니다...
where winget >nul 2>&1
if errorlevel 1 goto install_from_web
winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
call :find_python
if defined PYEXE goto have_python
:install_from_web
echo        python.org에서 설치 파일을 내려받습니다...
set "PYINST=%TEMP%\python-3.12.10-amd64.exe"
curl -L --fail -o "%PYINST%" "%PYTHON_URL%"
if errorlevel 1 goto fail_python
"%PYINST%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_test=0
del "%PYINST%" >nul 2>&1
call :find_python
if not defined PYEXE goto fail_python
:have_python
echo [1/3] Python 확인: %PYEXE%

rem --- 2. private venv and packages ---
if exist "%VPY%" goto have_venv
echo [2/3] 처음 실행이라 전용 실행 환경을 만듭니다...
if not exist "%HOME_DIR%" mkdir "%HOME_DIR%"
"%PYEXE%" -m venv "%VENV%"
if errorlevel 1 goto fail_install
:have_venv
fc /b requirements.txt "%VENV%\req.stamp" >nul 2>&1
if not errorlevel 1 goto base_ok
echo [2/3] 필요한 패키지를 설치합니다. 인터넷이 연결되어 있어야 합니다...
"%VPY%" -m pip install --disable-pip-version-check -q --upgrade pip
"%VPY%" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 goto fail_install
copy /y requirements.txt "%VENV%\req.stamp" >nul
:base_ok
echo [2/3] 패키지 준비 완료

rem --- desktop shortcut (first run only) ---
if defined GY_NO_SHORTCUT goto shortcut_done
if exist "%VENV%\shortcut.stamp" goto shortcut_done
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0make_shortcut.ps1" -Target "%~f0"
if not errorlevel 1 echo done> "%VENV%\shortcut.stamp"
:shortcut_done

rem --- 3. start the server ---
echo [3/3] 방송 서버를 시작합니다: http://localhost:%PORT%
echo        이 창을 닫으면 방송 화면도 멈춥니다. 방송을 마치면 창을 닫으세요.
echo.
if not defined GY_NO_BROWSER start "" /min cmd /c "timeout /t 4 /nobreak >nul & start http://localhost:%PORT%"
"%VPY%" -m uvicorn app:app --host 127.0.0.1 --port %PORT%
echo.
echo 서버가 종료되었습니다.
pause
exit /b 0

:find_python
set "PYEXE="
for /f "delims=" %%i in ('py -3.12 -c "import sys;print(sys.executable)" 2^>nul') do set "PYEXE=%%i"
if defined PYEXE exit /b 0
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if defined PYEXE exit /b 0
if exist "%ProgramFiles%\Python312\python.exe" set "PYEXE=%ProgramFiles%\Python312\python.exe"
exit /b 0

:fail_python
echo.
echo [오류] Python을 자동으로 설치하지 못했습니다.
echo        https://www.python.org/downloads/ 에서 Python 3.12을 설치한 뒤 다시 실행해 주세요.
echo        설치 첫 화면에서 "Add python.exe to PATH"를 꼭 체크하세요.
pause
exit /b 1

:fail_install
echo.
echo [오류] 패키지 설치에 실패했습니다. 인터넷 연결을 확인한 뒤 다시 실행해 주세요.
echo        계속 실패하면 %HOME_DIR% 폴더를 지우고 다시 실행해 보세요.
pause
exit /b 1
