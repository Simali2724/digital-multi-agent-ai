$ErrorActionPreference = 'Stop'

try {
    $response = Invoke-WebRequest `
        -Uri 'http://127.0.0.1:3000' `
        -TimeoutSec 2 `
        -UseBasicParsing

    if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
        Write-Host 'Frontend is already running on 127.0.0.1:3000'
        exit 0
    }
}
catch {
    Write-Host 'Starting frontend...'
}

Set-Location -LiteralPath (Join-Path $PSScriptRoot 'frontend')

if (-not (Test-Path 'node_modules')) {
    throw 'Frontend dependencies not found. Run npm install first.'
}

& npm.cmd run dev -- --hostname 127.0.0.1
