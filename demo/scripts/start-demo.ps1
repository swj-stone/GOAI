$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Python = Join-Path $ProjectRoot 'venv\Scripts\python.exe'
$EnvFile = Join-Path $ProjectRoot 'demo\.env.local'

if (-not (Test-Path $Python)) {
    throw "Project virtual environment not found: $Python"
}

if (Test-Path $EnvFile) {
    foreach ($line in [IO.File]::ReadAllLines($EnvFile)) {
        if ($line -match '^(?<name>[A-Z0-9_]+)=(?<value>.*)$') {
            [Environment]::SetEnvironmentVariable(
                $Matches.name,
                $Matches.value,
                [EnvironmentVariableTarget]::Process
            )
        }
    }
}

Push-Location $ProjectRoot
try {
    & $Python -m uvicorn campusmatch.main:app --app-dir demo/src --host 0.0.0.0 --port 3100
}
finally {
    Pop-Location
}
