$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Python = Join-Path $ProjectRoot 'venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    throw "Project virtual environment not found: $Python"
}

& $Python --version
& $Python -m pip check

$required = @(
    'demo\fixtures\student-materials.md',
    'demo\fixtures\job-general-operations.md',
    'demo\agentteams\mcp-campusmatch.yaml'
)

foreach ($relative in $required) {
    $path = Join-Path $ProjectRoot $relative
    if (-not (Test-Path $path)) {
        throw "Demo file missing: $relative"
    }
}

foreach ($port in @(18001, 18080, 18088, 18888)) {
    $open = Test-NetConnection -ComputerName 127.0.0.1 -Port $port -InformationLevel Quiet
    $state = if ($open) { 'OK' } else { 'OFFLINE_ONLY' }
    Write-Output "HiClaw port $port`: $state"
}

Write-Output 'CampusMatch preflight: PASS'
