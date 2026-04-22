$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvPath = Join-Path $repoRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\\python.exe"
$configPath = Join-Path $repoRoot "config.json"
$configExamplePath = Join-Path $repoRoot "config.example.json"
$requirementsPath = Join-Path $repoRoot "requirements.txt"

function Get-HostPython {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @($python.Source)
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return @($py.Source, "-3")
    }

    throw "Python 3.10+ is required but no 'python' or 'py' launcher was found in PATH."
}

$hostPython = Get-HostPython

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment in $venvPath"
    if ($hostPython.Length -gt 1) {
        & $hostPython[0] $hostPython[1] -m venv $venvPath
    } else {
        & $hostPython[0] -m venv $venvPath
    }
}

Write-Host "Installing dependencies"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r $requirementsPath

if (-not (Test-Path $configPath)) {
    Copy-Item $configExamplePath $configPath
    Write-Host "Created config.json from config.example.json"
} else {
    Write-Host "config.json already exists"
}

Write-Host ""
Write-Host "Bootstrap complete."
Write-Host "Next steps:"
Write-Host "1. Edit config.json if you want local default SSH settings."
Write-Host "2. Start the API with:"
Write-Host "   $venvPython run.py"
Write-Host "3. Open http://localhost:8754/docs once it is running."
