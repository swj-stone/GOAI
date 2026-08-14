param()

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Helper = Join-Path $ProjectRoot 'demo\agentteams\configure-worker-mcp.sh'
$Workers = @(
    'career-navigator',
    'profile-agent',
    'job-agent',
    'match-agent',
    'coach-agent',
    'audit-agent'
)

foreach ($worker in $Workers) {
    $container = 'agentteams-worker-' + $worker
    docker cp $Helper ("${container}:/tmp/configure-worker-mcp.sh")
    if ($LASTEXITCODE -ne 0) {
        throw ("Failed to copy MCP helper to " + $container)
    }

    docker exec $container bash /tmp/configure-worker-mcp.sh $worker
    if ($LASTEXITCODE -ne 0) {
        throw ("Failed to configure MCP for " + $worker)
    }

    $agentDir = '/root/agentteams-fs/agents/' + $worker
    $metadataText = docker exec -w $agentDir $container timeout 15s mcporter list mcp-campusmatch --json
    if ($LASTEXITCODE -ne 0) {
        throw ("Failed to discover MCP from " + $worker)
    }
    $metadata = $metadataText | ConvertFrom-Json
    if ($metadata.name -ne 'mcp-campusmatch' -or $metadata.status -ne 'ok') {
        throw ("MCP health verification failed for " + $worker)
    }
    Write-Output ($worker + ': MCP_HEALTHY')
}

Write-Output 'CampusMatch MCP configuration was written for all six Workers.'
