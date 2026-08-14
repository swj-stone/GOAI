param([string]$TaskId = '')

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Helper = Join-Path $ProjectRoot 'demo\agentteams\delegate-team-smoke.sh'
$Materials = Join-Path $ProjectRoot 'demo\fixtures\student-materials.md'
$Job = Join-Path $ProjectRoot 'demo\fixtures\job-general-operations.md'

if (-not $TaskId) {
    $TaskId = 'team-live-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
}
if ($TaskId -notmatch '^[A-Za-z0-9_-]+$') {
    throw 'TaskId may only contain letters, numbers, underscores, and hyphens.'
}

$copies = @(
    @($Helper, '/tmp/delegate-team-smoke.sh'),
    @($Materials, '/tmp/student-materials.md'),
    @($Job, '/tmp/job-general-operations.md')
)

foreach ($copy in $copies) {
    docker cp $copy[0] ("agentteams-manager:" + $copy[1])
    if ($LASTEXITCODE -ne 0) {
        throw ("Failed to copy delegation asset: " + $copy[0])
    }
}

docker exec agentteams-manager bash /tmp/delegate-team-smoke.sh $TaskId
if ($LASTEXITCODE -ne 0) {
    throw 'CampusMatch Team delegation failed.'
}

Write-Output ("TASK_ID=" + $TaskId)
