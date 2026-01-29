# Spread Eagle Dev Environment Manager
# Usage: .\dev.ps1 [start|stop|status|restart]

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "status", "restart", "kill")]
    [string]$Action = "status"
)

$API_PORT = 8000
$UI_PORT = 3000
$PROJECT_ROOT = $PSScriptRoot

function Get-PortProcess {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        return @{
            PID = $conn.OwningProcess
            Name = $proc.ProcessName
            Running = $true
        }
    }
    return @{ Running = $false }
}

function Show-Status {
    Write-Host "`n=== Spread Eagle Dev Status ===" -ForegroundColor Cyan
    Write-Host ""

    # API
    $api = Get-PortProcess -Port $API_PORT
    if ($api.Running) {
        Write-Host "  API (port $API_PORT): " -NoNewline
        Write-Host "RUNNING" -ForegroundColor Green -NoNewline
        Write-Host " (PID $($api.PID))"
    } else {
        Write-Host "  API (port $API_PORT): " -NoNewline
        Write-Host "STOPPED" -ForegroundColor Red
    }

    # UI
    $ui = Get-PortProcess -Port $UI_PORT
    if ($ui.Running) {
        Write-Host "  UI  (port $UI_PORT): " -NoNewline
        Write-Host "RUNNING" -ForegroundColor Green -NoNewline
        Write-Host " (PID $($ui.PID))"
    } else {
        Write-Host "  UI  (port $UI_PORT): " -NoNewline
        Write-Host "STOPPED" -ForegroundColor Red
    }

    # Docker/Airflow
    $docker = docker ps --filter "name=airflow" --format "{{.Names}}" 2>$null
    if ($docker) {
        Write-Host "  Airflow: " -NoNewline
        Write-Host "RUNNING" -ForegroundColor Green
    } else {
        Write-Host "  Airflow: " -NoNewline
        Write-Host "STOPPED" -ForegroundColor Red
    }

    # Config check
    Write-Host ""
    Write-Host "=== Configuration ===" -ForegroundColor Cyan

    # Check .env for DB
    $envFile = Join-Path $PROJECT_ROOT ".env"
    if (Test-Path $envFile) {
        $dbHost = (Get-Content $envFile | Select-String "DB_HOST=").ToString().Split("=")[1]
        if ($dbHost -like "*rds.amazonaws.com*") {
            Write-Host "  .env DB_HOST: " -NoNewline
            Write-Host "RDS" -ForegroundColor Green -NoNewline
            Write-Host " ($dbHost)"
        } else {
            Write-Host "  .env DB_HOST: " -NoNewline
            Write-Host "LOCAL" -ForegroundColor Yellow -NoNewline
            Write-Host " ($dbHost) - Should be RDS!"
        }
    }

    # Check ui/.env.local for API URL
    $uiEnvFile = Join-Path $PROJECT_ROOT "ui\.env.local"
    if (Test-Path $uiEnvFile) {
        $apiUrl = (Get-Content $uiEnvFile | Select-String "NEXT_PUBLIC_API_URL=").ToString().Split("=")[1]
        $configuredPort = if ($apiUrl -match ":(\d+)") { $matches[1] } else { "unknown" }

        Write-Host "  ui/.env.local API: " -NoNewline
        if ($configuredPort -eq $API_PORT.ToString()) {
            Write-Host "OK" -ForegroundColor Green -NoNewline
            Write-Host " ($apiUrl)"
        } else {
            Write-Host "MISMATCH!" -ForegroundColor Red -NoNewline
            Write-Host " ($apiUrl) - API runs on port $API_PORT!"
        }
    } else {
        Write-Host "  ui/.env.local: " -NoNewline
        Write-Host "MISSING" -ForegroundColor Red
    }

    Write-Host ""
}

function Stop-Dev {
    Write-Host "`nStopping dev services..." -ForegroundColor Yellow

    # Kill by port
    $api = Get-PortProcess -Port $API_PORT
    if ($api.Running) {
        Stop-Process -Id $api.PID -Force -ErrorAction SilentlyContinue
        Write-Host "  Stopped API (PID $($api.PID))" -ForegroundColor Green
    }

    $ui = Get-PortProcess -Port $UI_PORT
    if ($ui.Running) {
        Stop-Process -Id $ui.PID -Force -ErrorAction SilentlyContinue
        Write-Host "  Stopped UI (PID $($ui.PID))" -ForegroundColor Green
    }

    Write-Host "Done.`n" -ForegroundColor Green
}

function Kill-All {
    Write-Host "`nKilling ALL node and python processes..." -ForegroundColor Red

    Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

    Write-Host "Done. All node/python processes killed.`n" -ForegroundColor Green
}

function Test-Config {
    $errors = @()

    # Check UI env points to correct API port
    $uiEnvFile = Join-Path $PROJECT_ROOT "ui\.env.local"
    if (Test-Path $uiEnvFile) {
        $apiUrl = (Get-Content $uiEnvFile | Select-String "NEXT_PUBLIC_API_URL=").ToString().Split("=")[1]
        if ($apiUrl -notmatch ":$API_PORT") {
            $errors += "ui/.env.local points to wrong port! Expected :$API_PORT, got: $apiUrl"
        }
    } else {
        $errors += "ui/.env.local is missing!"
    }

    # Check .env points to RDS
    $envFile = Join-Path $PROJECT_ROOT ".env"
    if (Test-Path $envFile) {
        $dbHost = (Get-Content $envFile | Select-String "DB_HOST=").ToString().Split("=")[1]
        if ($dbHost -notlike "*rds.amazonaws.com*") {
            $errors += ".env DB_HOST is not RDS: $dbHost"
        }
    }

    return $errors
}

function Start-Dev {
    Write-Host "`nValidating configuration..." -ForegroundColor Yellow
    $errors = Test-Config

    if ($errors.Count -gt 0) {
        Write-Host "`n  CONFIG ERRORS:" -ForegroundColor Red
        foreach ($err in $errors) {
            Write-Host "    - $err" -ForegroundColor Red
        }
        Write-Host "`nFix these before starting!`n" -ForegroundColor Red
        return
    }
    Write-Host "  Config OK" -ForegroundColor Green

    Write-Host "`nStarting dev services..." -ForegroundColor Yellow

    # Start API
    $api = Get-PortProcess -Port $API_PORT
    if (-not $api.Running) {
        Write-Host "  Starting API on port $API_PORT..."
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PROJECT_ROOT'; .\.venv312\Scripts\Activate.ps1; uvicorn spread_eagle.api.main:app --reload --port $API_PORT"
    } else {
        Write-Host "  API already running"
    }

    # Start UI
    $ui = Get-PortProcess -Port $UI_PORT
    if (-not $ui.Running) {
        Write-Host "  Starting UI on port $UI_PORT..."
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PROJECT_ROOT\ui'; npm run dev"
    } else {
        Write-Host "  UI already running"
    }

    Start-Sleep -Seconds 2
    Write-Host "`nServices starting. Check status with: .\dev.ps1 status`n" -ForegroundColor Green
}

# Main
switch ($Action) {
    "status" { Show-Status }
    "stop" { Stop-Dev; Show-Status }
    "start" { Start-Dev }
    "restart" { Stop-Dev; Start-Sleep -Seconds 1; Start-Dev }
    "kill" { Kill-All; Show-Status }
}
