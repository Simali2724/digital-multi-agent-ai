$ErrorActionPreference = 'Stop'

$env:OLLAMA_MODELS = 'D:\ollama-models'
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_KEEP_ALIVE = '30m'

try {
    $null = Invoke-RestMethod `
        -Uri 'http://127.0.0.1:11434/api/version' `
        -TimeoutSec 2

    Write-Host 'Ollama is already running on 127.0.0.1:11434'
    exit 0
}
catch {
    Write-Host 'Starting Ollama...'
}

$ollamaExe = Join-Path `
    $env:LOCALAPPDATA `
    'Programs\Ollama\ollama.exe'

if (-not (Test-Path $ollamaExe)) {
    throw "Ollama executable not found: $ollamaExe"
}

& $ollamaExe serve
