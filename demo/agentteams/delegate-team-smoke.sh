#!/usr/bin/env bash
set -euo pipefail

task_id="${1:?task id is required}"
materials_file="${2:-/tmp/student-materials.md}"
job_file="${3:-/tmp/job-general-operations.md}"
team_name="campusmatch-demo"
leader_name="career-navigator"
title="CampusMatch synthetic evidence pipeline smoke test"
task_dir="/root/agentteams-fs/shared/tasks/${task_id}"
creds_file="/root/manager-workspace/.openclaw/credentials/matrix/credentials.json"
state_script="/opt/agentteams/agent/skills/task-management/scripts/manage-state.sh"

if [[ ! "$task_id" =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$ ]]; then
  echo "Task ID contains unsupported characters." >&2
  exit 2
fi

if [[ -e "$task_dir" ]]; then
  echo "Task directory already exists: ${task_dir}" >&2
  exit 3
fi

mkdir -p "$task_dir/base"
cp "$materials_file" "$task_dir/base/student-materials.md"
cp "$job_file" "$task_dir/base/job-general-operations.md"

jq -n \
  --arg task_id "$task_id" \
  --arg title "$title" \
  --arg assigned_to "$leader_name" \
  --arg team "$team_name" \
  --arg created_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{
    task_id: $task_id,
    type: "finite",
    status: "assigned",
    title: $title,
    assigned_to: $assigned_to,
    delegated_to_team: $team,
    created_at: $created_at
  }' > "$task_dir/meta.json"

cat > "$task_dir/spec.md" <<EOF
# CampusMatch Team smoke test

## Objective

Use the CampusMatch Team and its assigned custom Skills to run the complete evidence pipeline on the two synthetic files under \`base/\`. This is a functional test, not a hiring decision.

## Required flow

1. Profile Agent reads \`base/student-materials.md\` and calls \`mcp-campusmatch.profile_materials\` with task ID \`${task_id}\`.
2. Job Agent reads \`base/job-general-operations.md\` and calls \`mcp-campusmatch.parse_job\` with the same task ID and mode \`job_search\`.
3. Match Agent calls \`mcp-campusmatch.match_evidence\` only after Profile and Job complete.
4. Coach Agent calls \`mcp-campusmatch.generate_coaching\` only after Match completes and must not invent experience.
5. Audit Agent calls \`mcp-campusmatch.audit_export\` with consent=true, trace=true, human_approved=false. The expected gate is BLOCK because human approval is intentionally absent.
6. Team Leader writes \`result.md\` with the five stage outcomes, match score, evidence coverage, Audit status, and any blocker. Push the result to shared storage and @mention Manager when complete.

## Acceptance criteria

- All tool calls use the exact registered server name \`mcp-campusmatch\`.
- The expected deterministic values are match score 77 and evidence coverage 85.
- The policy-risk gender condition remains visible as POLICY_EXCLUDED and never participates in scoring.
- Final Audit status is BLOCK with APPROVAL_REQUIRED; do not bypass the human gate.
- No real personal data is present; all inputs are synthetic.
EOF

for file in meta.json spec.md base/student-materials.md base/job-general-operations.md; do
  mc cp "$task_dir/$file" "${AGENTTEAMS_STORAGE_PREFIX}/shared/tasks/${task_id}/${file}" >/dev/null
done

leader_json="$(agt get workers "$leader_name" -o json)"
room_id="$(echo "$leader_json" | jq -r '.roomID')"
leader_matrix_id="$(echo "$leader_json" | jq -r '.matrixUserID')"

bash "$state_script" \
  --action add-finite \
  --task-id "$task_id" \
  --title "$title" \
  --assigned-to "$leader_name" \
  --room-id "$room_id" \
  --delegated-to-team "$team_name" >/dev/null

access_token="$(jq -r '.accessToken' "$creds_file")"
homeserver="$(jq -r '.homeserver' "$creds_file")"
encoded_room="$(jq -rn --arg value "$room_id" '$value | @uri')"
transaction_id="$(jq -rn --arg value "${task_id}-dispatch-$(date +%s)" '$value | @uri')"
message="${leader_matrix_id} New task [${task_id}]: ${title}. Use your file-sync skill to pull shared/tasks/${task_id}/spec.md. Decompose and assign to your team. @mention me when complete."
formatted_message="<a href=\"https://matrix.to/#/${leader_matrix_id}\">${leader_matrix_id}</a> New task [${task_id}]: ${title}. Use your file-sync skill to pull shared/tasks/${task_id}/spec.md. Decompose and assign to your team. @mention me when complete."
body="$(jq -n --arg body "$message" --arg formatted "$formatted_message" --arg user "$leader_matrix_id" '{msgtype:"m.text",body:$body,format:"org.matrix.custom.html",formatted_body:$formatted,"m.mentions":{user_ids:[$user]}}')"

curl -fsS -X PUT \
  "${homeserver}/_matrix/client/v3/rooms/${encoded_room}/send/m.room.message/${transaction_id}" \
  -H "Authorization: Bearer ${access_token}" \
  -H 'Content-Type: application/json' \
  --data "$body" >/dev/null

echo "Delegated ${task_id} to Team Leader ${leader_name}."
