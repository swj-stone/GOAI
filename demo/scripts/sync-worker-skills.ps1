param()

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$SkillRoot = Join-Path $ProjectRoot 'demo\agentteams\skills'
$Assignments = @(
    @('career-navigator', 'campusmatch-orchestrate'),
    @('profile-agent', 'campusmatch-profile'),
    @('job-agent', 'campusmatch-job'),
    @('match-agent', 'campusmatch-match'),
    @('coach-agent', 'campusmatch-coach'),
    @('audit-agent', 'campusmatch-audit')
)

docker cp (Join-Path $SkillRoot '.') agentteams-manager:/root/manager-workspace/worker-skills/
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to update the Manager canonical worker-skills directory.'
}

foreach ($assignment in $Assignments) {
    $worker = $assignment[0]
    $skill = $assignment[1]
    $container = 'agentteams-worker-' + $worker
    $source = Join-Path $SkillRoot $skill
    $targetRoot = '/root/agentteams-fs/agents/' + $worker + '/skills'
    $targetFile = $targetRoot + '/' + $skill + '/SKILL.md'

    docker exec agentteams-manager bash /opt/agentteams/agent/skills/worker-management/scripts/push-worker-skills.sh --worker $worker --no-notify
    if ($LASTEXITCODE -ne 0) {
        throw ("Official Worker spec update failed for " + $worker)
    }

    docker exec $container mkdir -p $targetRoot
    if ($LASTEXITCODE -ne 0) {
        throw ("Failed to prepare the Worker skill directory for " + $worker)
    }

    docker cp $source ("${container}:${targetRoot}/")
    if ($LASTEXITCODE -ne 0) {
        throw ("Failed to sync " + $skill + " to " + $worker)
    }

    $localHash = (Get-FileHash (Join-Path $source 'SKILL.md') -Algorithm SHA256).Hash.ToLowerInvariant()
    $remoteHash = (docker exec $container sha256sum $targetFile).Split(' ')[0].ToLowerInvariant()
    if ($LASTEXITCODE -ne 0 -or $remoteHash -ne $localHash) {
        throw ("Skill checksum verification failed for " + $worker)
    }
    Write-Output ($worker + ':' + $skill + ':SYNCED')
}

Write-Output 'All CampusMatch Worker Skills are synchronized and checksum-verified.'
