param([string]$TaskId = 'smoke-campusmatch')

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$SmokeScript = Join-Path $ProjectRoot 'demo\agentteams\smoke-test-campusmatch.sh'
$Materials = Join-Path $ProjectRoot 'demo\fixtures\student-materials.md'
$Job = Join-Path $ProjectRoot 'demo\fixtures\job-general-operations.md'

if ($TaskId -notmatch '^[A-Za-z0-9_-]+$') {
    throw 'TaskId may only contain letters, numbers, underscores, and hyphens.'
}

$copies = @(
    @($SmokeScript, '/tmp/smoke-test-campusmatch.sh'),
    @($Materials, '/tmp/student-materials.md'),
    @($Job, '/tmp/job-general-operations.md')
)

foreach ($copy in $copies) {
    docker cp $copy[0] ("agentteams-manager:" + $copy[1])
    if ($LASTEXITCODE -ne 0) {
        throw ("Failed to copy smoke-test asset: " + $copy[0])
    }
}

docker exec agentteams-manager bash /tmp/smoke-test-campusmatch.sh $TaskId
if ($LASTEXITCODE -ne 0) {
    throw 'CampusMatch MCP smoke test failed.'
}
