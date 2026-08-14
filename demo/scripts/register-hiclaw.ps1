param([string]$Token)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Yaml = Join-Path $ProjectRoot 'demo\agentteams\mcp-campusmatch.yaml'
$RegisterHelper = Join-Path $ProjectRoot 'demo\agentteams\register-campusmatch.sh'
$EnvFile = Join-Path $ProjectRoot 'demo\.env.local'

if (-not (Test-Path $Yaml)) {
    throw "MCP configuration not found: $Yaml"
}

if (-not (Test-Path $RegisterHelper)) {
    throw "MCP registration helper not found: $RegisterHelper"
}

if (-not $Token -and (Test-Path $EnvFile)) {
    $saved = [IO.File]::ReadAllLines($EnvFile) | Where-Object { $_ -like 'CAMPUSMATCH_MCP_TOKEN=*' } | Select-Object -First 1
    if ($saved) {
        $Token = $saved.Substring('CAMPUSMATCH_MCP_TOKEN='.Length)
    }
}

if (-not $Token) {
    $bytes = New-Object byte[] 32
    $generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($bytes)
    }
    finally {
        $generator.Dispose()
    }
    $Token = -join ($bytes | ForEach-Object { $_.ToString('x2') })
    [IO.File]::WriteAllText($EnvFile, "CAMPUSMATCH_MCP_TOKEN=$Token`n", [Text.UTF8Encoding]::new($false))
}

docker cp $Yaml agentteams-manager:/tmp/mcp-campusmatch.yaml
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to copy CampusMatch MCP YAML into the Manager container.'
}

docker cp $RegisterHelper agentteams-manager:/tmp/register-campusmatch.sh
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to copy the CampusMatch registration helper into the Manager container.'
}

docker exec agentteams-manager bash /tmp/register-campusmatch.sh campusmatch $Token --yaml-file /tmp/mcp-campusmatch.yaml
if ($LASTEXITCODE -ne 0) {
    throw 'CampusMatch MCP registration failed inside the Manager container.'
}

Write-Output 'CampusMatch MCP registered. The token is stored in ignored demo/.env.local and was not printed.'
Write-Output 'Start the Demo, then verify with: docker exec agentteams-manager mcporter list mcp-campusmatch --schema'
