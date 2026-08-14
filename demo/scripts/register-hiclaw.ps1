param([string]$Token)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Yaml = Join-Path $ProjectRoot 'demo\agentteams\mcp-campusmatch.yaml'
$EnvFile = Join-Path $ProjectRoot 'demo\.env.local'

if (-not (Test-Path $Yaml)) {
    throw "MCP configuration not found: $Yaml"
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

docker exec agentteams-manager bash -lc 'set -e; export HIGRESS_CONSOLE_URL=http://agentteams-controller:8001; source /opt/agentteams/scripts/lib/gateway-api.sh; gateway_ensure_session; awk ''{gsub("http://127[.]0[.]0[.]1:8001", "http://agentteams-controller:8001"); print}'' /opt/agentteams/agent/skills/mcp-server-management/scripts/setup-mcp-server.sh > /tmp/setup-mcp-server-campusmatch.sh; bash /tmp/setup-mcp-server-campusmatch.sh "$@"' campusmatch campusmatch $Token --yaml-file /tmp/mcp-campusmatch.yaml
if ($LASTEXITCODE -ne 0) {
    throw 'CampusMatch MCP registration failed inside the Manager container.'
}

Write-Output 'CampusMatch MCP registered. The token is stored in ignored demo/.env.local and was not printed.'
Write-Output 'Start the Demo, then verify with: docker exec agentteams-manager mcporter list campusmatch --schema'
