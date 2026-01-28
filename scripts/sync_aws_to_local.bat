@echo off
REM ============================================================
REM Spread Eagle: Sync AWS RDS to Local PostgreSQL
REM ============================================================
REM This script:
REM   1. Creates local spread_eagle database (if not exists)
REM   2. Dumps the cbb schema from AWS RDS
REM   3. Restores it to local PostgreSQL
REM ============================================================

setlocal

REM --- Configuration ---
set PG_BIN=C:\Program Files\PostgreSQL\18\bin
set LOCAL_HOST=localhost
set LOCAL_PORT=5432
set LOCAL_USER=postgres
set LOCAL_DB=spread_eagle

REM AWS RDS (from your .env)
set AWS_HOST=spread-eagle-db.cbwyw8ky62xm.us-east-2.rds.amazonaws.com
set AWS_PORT=5432
set AWS_USER=postgres
set AWS_DB=postgres

REM Temp file for dump
set DUMP_FILE=%TEMP%\spread_eagle_cbb_dump.sql

echo.
echo ============================================================
echo   Spread Eagle: AWS to Local Sync
echo ============================================================
echo.

REM --- Step 1: Create local database ---
echo [Step 1/4] Creating local database '%LOCAL_DB%'...
"%PG_BIN%\psql" -h %LOCAL_HOST% -p %LOCAL_PORT% -U %LOCAL_USER% -c "CREATE DATABASE %LOCAL_DB%;" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   Created new database.
) else (
    echo   Database already exists (OK).
)

REM --- Step 2: Create cbb schema locally ---
echo [Step 2/4] Creating cbb schema locally...
"%PG_BIN%\psql" -h %LOCAL_HOST% -p %LOCAL_PORT% -U %LOCAL_USER% -d %LOCAL_DB% -c "CREATE SCHEMA IF NOT EXISTS cbb;"

REM --- Step 3: Dump from AWS ---
echo [Step 3/4] Dumping 'cbb' schema from AWS RDS...
echo   (This may take a few minutes depending on data size)
echo   Host: %AWS_HOST%
set PGPASSWORD=Sport4788!
"%PG_BIN%\pg_dump" -h %AWS_HOST% -p %AWS_PORT% -U %AWS_USER% -d %AWS_DB% -n cbb --no-owner --no-acl -f "%DUMP_FILE%"

if %ERRORLEVEL% NEQ 0 (
    echo   ERROR: Failed to dump from AWS. Check your connection.
    exit /b 1
)
echo   Dump complete: %DUMP_FILE%

REM --- Step 4: Restore locally ---
echo [Step 4/4] Restoring to local database...
"%PG_BIN%\psql" -h %LOCAL_HOST% -p %LOCAL_PORT% -U %LOCAL_USER% -d %LOCAL_DB% -f "%DUMP_FILE%"

if %ERRORLEVEL% NEQ 0 (
    echo   WARNING: Some errors during restore (may be OK if tables already exist)
)

echo.
echo ============================================================
echo   DONE! Local database is ready.
echo ============================================================
echo.
echo   Local connection string:
echo   postgresql://postgres:YOUR_LOCAL_PASSWORD@localhost:5432/spread_eagle
echo.
echo   Next steps:
echo   1. Update your .env to use local database
echo   2. Restart your API server
echo.

endlocal
pause
