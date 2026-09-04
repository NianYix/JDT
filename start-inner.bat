@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "LOG=%~dp0start.log"
echo ==== start %DATE% %TIME% ==== > "%LOG%"

echo ========================================
echo  AI Engineering Copilot - One Click Start
echo ========================================
echo.
echo Log file: %LOG%
echo.

set "USE_SQLITE=1"
set "DB_URL=sqlite+pysqlite:///./aec_local.db"

call :step_env
if errorlevel 1 goto :end_fail

call :step_docker
REM docker failure is OK, we keep SQLite

call :step_venv
if errorlevel 1 goto :end_fail

call :step_db
if errorlevel 1 goto :end_fail

call :step_frontend
if errorlevel 1 goto :end_fail

call :step_launch
goto :end_ok

:step_env
echo [1/5] Checking .env ...
>>"%LOG%" echo [1/5] Checking .env
if exist ".env" (
  echo [OK] .env exists
  exit /b 0
)
if not exist ".env.example" (
  echo [ERROR] .env.example missing
  >>"%LOG%" echo ERROR: .env.example missing
  exit /b 1
)
copy /Y ".env.example" ".env" >nul
echo [OK] Created .env
>>"%LOG%" echo Created .env
exit /b 0

:step_docker
echo [2/5] Looking for Docker ...
>>"%LOG%" echo [2/5] Looking for Docker
set "DOCKER_CMD="
where docker >nul 2>nul
if not errorlevel 1 set "DOCKER_CMD=docker"

if not defined DOCKER_CMD (
  if exist "C:\Program Files\Docker\Docker\resources\bin\docker.exe" (
    set "DOCKER_CMD=C:\Program Files\Docker\Docker\resources\bin\docker.exe"
  )
)

if not defined DOCKER_CMD (
  echo [WARN] Docker not found, use SQLite
  >>"%LOG%" echo Docker not found, USE_SQLITE=1
  set "USE_SQLITE=1"
  exit /b 0
)

echo [INFO] Docker found: !DOCKER_CMD!
>>"%LOG%" echo Docker found: !DOCKER_CMD!
echo [INFO] docker compose up -d ...
"!DOCKER_CMD!" compose up -d >>"%LOG%" 2>&1
if errorlevel 1 (
  echo [WARN] compose failed, use SQLite
  >>"%LOG%" echo compose failed
  set "USE_SQLITE=1"
  exit /b 0
)

echo [INFO] Waiting Postgres ...
set "PG_READY=0"
for /L %%i in (1,1,20) do (
  if "!PG_READY!"=="0" (
    "!DOCKER_CMD!" compose exec -T postgres pg_isready -U aec -d aec >nul 2>nul
    if not errorlevel 1 set "PG_READY=1"
    if "!PG_READY!"=="0" timeout /t 1 /nobreak >nul
  )
)

if "!PG_READY!"=="1" (
  echo [OK] Postgres ready, use PostgreSQL
  >>"%LOG%" echo Postgres ready
  set "USE_SQLITE=0"
  set "DB_URL="
) else (
  echo [WARN] Postgres not ready, use SQLite
  >>"%LOG%" echo Postgres not ready
  set "USE_SQLITE=1"
)
exit /b 0

:step_venv
echo [3/5] Checking backend venv ...
>>"%LOG%" echo [3/5] venv
set "VENV_OK=0"
if exist "backend\.venv\Scripts\python.exe" (
  backend\.venv\Scripts\python.exe --version >>"%LOG%" 2>&1
  if not errorlevel 1 (
    backend\.venv\Scripts\python.exe -c "import pydantic" >>"%LOG%" 2>&1
    if not errorlevel 1 set "VENV_OK=1"
  )
)
if "!VENV_OK!"=="1" (
  echo [OK] backend\.venv ready
  exit /b 0
)

if exist "backend\.venv\" (
  echo [WARN] venv missing/broken or deps incomplete, recreating ...
  >>"%LOG%" echo venv recreate required
  rmdir /s /q "backend\.venv"
)

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] python not in PATH
  >>"%LOG%" echo ERROR: python missing
  exit /b 1
)

echo [INFO] Creating venv and installing deps ...
pushd backend
python -m venv .venv >>"%LOG%" 2>&1
if errorlevel 1 (
  popd
  echo [ERROR] venv create failed
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install -U pip >>"%LOG%" 2>&1
pip install -e ".[dev]" >>"%LOG%" 2>&1
if errorlevel 1 (
  popd
  echo [ERROR] pip install failed, see start.log
  exit /b 1
)
popd
echo [OK] Backend venv ready
exit /b 0

:step_db
echo [4/5] Preparing database ...
>>"%LOG%" echo [4/5] db USE_SQLITE=!USE_SQLITE!
pushd backend
call .venv\Scripts\activate.bat

if "!USE_SQLITE!"=="1" (
  set "DATABASE_URL=!DB_URL!"
  echo [INFO] Init SQLite: !DATABASE_URL!
  python -m scripts.init_db >>"%LOG%" 2>&1
  if errorlevel 1 (
    popd
    echo [ERROR] init_db failed, see start.log
    exit /b 1
  )
  echo [OK] SQLite ready: backend\aec_local.db
) else (
  echo [INFO] alembic upgrade head ...
  alembic upgrade head >>"%LOG%" 2>&1
  if errorlevel 1 (
    popd
    echo [ERROR] alembic failed, see start.log
    exit /b 1
  )
  echo [OK] Migrations applied
)
popd
exit /b 0

:step_frontend
echo [5/5] Checking frontend deps ...
>>"%LOG%" echo [5/5] frontend
if exist "frontend\node_modules\" (
  echo [OK] frontend\node_modules found
  exit /b 0
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm not in PATH
  >>"%LOG%" echo ERROR: npm missing
  exit /b 1
)

echo [INFO] npm install ...
pushd frontend
call npm install --registry=https://registry.npmmirror.com >>"%LOG%" 2>&1
if errorlevel 1 (
  call npm install >>"%LOG%" 2>&1
)
if errorlevel 1 (
  popd
  echo [ERROR] npm install failed, see start.log
  exit /b 1
)
popd
echo [OK] frontend ready
exit /b 0

:step_launch
echo.
echo [INFO] Stopping old Backend on port 8000 if any ...
>>"%LOG%" echo stop old backend :8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
  taskkill /F /PID %%a >>"%LOG%" 2>&1
)

echo [INFO] Starting Backend ...
>>"%LOG%" echo launch backend
if "!USE_SQLITE!"=="1" (
  start "AEC-Backend" cmd /k "cd /d "%~dp0backend" && call .venv\Scripts\activate.bat && set DATABASE_URL=sqlite+pysqlite:///./aec_local.db && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
) else (
  start "AEC-Backend" cmd /k "cd /d "%~dp0backend" && call .venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
)

timeout /t 2 /nobreak >nul

echo [INFO] Starting Frontend ...
>>"%LOG%" echo launch frontend
start "AEC-Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================
echo  Started successfully
if "!USE_SQLITE!"=="1" (
  echo  DB mode : SQLite local fallback
) else (
  echo  DB mode : PostgreSQL
)
echo  Health  : http://localhost:8000/health
echo  API Docs: http://localhost:8000/docs
echo  App     : http://localhost:5173
echo  Login   : http://localhost:5173/login
echo  Admin   : http://localhost:8000/admin
echo ========================================
>>"%LOG%" echo SUCCESS
exit /b 0

:end_fail
echo.
echo [FAILED] See log: %LOG%
echo.
pause
exit /b 1

:end_ok
echo.
pause
exit /b 0
