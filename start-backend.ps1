$ErrorActionPreference = 'Stop'

try {
    $health = Invoke-RestMethod `
        -Uri 'http://127.0.0.1:8000/health' `
        -TimeoutSec 2

    if ($health.status -eq 'ok') {
        Write-Host 'Backend is already running on 127.0.0.1:8000'
        exit 0
    }
}
catch {
    Write-Host 'Starting backend...'
}

Set-Location -LiteralPath (Join-Path $PSScriptRoot 'backend')

$pythonExe = Join-Path `
    $PSScriptRoot `
    'backend\.venv\Scripts\python.exe'

if (-not (Test-Path $pythonExe)) {
    throw "Backend Python executable not found: $pythonExe"
}

& $pythonExe -m uvicorn main:app --host 127.0.0.1 --port 8000
