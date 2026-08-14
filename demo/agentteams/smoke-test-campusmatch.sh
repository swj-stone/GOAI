#!/usr/bin/env bash
set -euo pipefail

task_id="${1:-smoke-campusmatch}"
materials_file="${2:-/tmp/student-materials.md}"
job_file="${3:-/tmp/job-general-operations.md}"
work_dir="/tmp/campusmatch-smoke-${task_id}"

if [[ ! "$task_id" =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$ ]]; then
  echo "Task ID contains unsupported characters." >&2
  exit 2
fi

mkdir -p "$work_dir"
materials="$(cat "$materials_file")"
job_description="$(cat "$job_file")"

run_tool() {
  local output_file="$1"
  local selector="$2"
  shift 2

  set +e
  timeout 15s mcporter call "$selector" "$@" > "$output_file"
  local status=$?
  set -e

  # mcporter 0.9.0 may print a completed response but retain the HTTP
  # connection. GNU timeout returns 124 in that compatibility case.
  if [[ $status -ne 0 && $status -ne 124 ]]; then
    printf 'Tool call failed: %s (exit %s)\n' "$selector" "$status" >&2
    cat "$output_file" >&2
    return "$status"
  fi
  jq -e . "$output_file" >/dev/null
}

run_tool "$work_dir/profile.json" mcp-campusmatch.profile_materials \
  "task_id:${task_id}" \
  "idempotency_key:${task_id}-profile-v1" \
  "user_id:S001" \
  "source_id:student-materials" \
  "markdown:${materials}"
jq -e '.user_id == "S001" and (.evidence | length > 0)' "$work_dir/profile.json" >/dev/null

run_tool "$work_dir/job.json" mcp-campusmatch.parse_job \
  "task_id:${task_id}" \
  "idempotency_key:${task_id}-job-v1" \
  "job_id:J001" \
  "mode:job_search" \
  "jd_markdown:${job_description}"
jq -e '.job_id == "J001" and (.requirements | length > 0)' "$work_dir/job.json" >/dev/null

run_tool "$work_dir/match.json" mcp-campusmatch.match_evidence \
  "task_id:${task_id}" \
  "idempotency_key:${task_id}-match-v1"
jq -e '.match_score == 77 and .evidence_coverage == 85' "$work_dir/match.json" >/dev/null

run_tool "$work_dir/coach.json" mcp-campusmatch.generate_coaching \
  "task_id:${task_id}" \
  "idempotency_key:${task_id}-coach-v1"
jq -e '(.resume_suggestions | length > 0) and (.interview_questions | length > 0)' "$work_dir/coach.json" >/dev/null

run_tool "$work_dir/audit-block.json" mcp-campusmatch.audit_export \
  "task_id:${task_id}" \
  "idempotency_key:${task_id}-audit-block-v1" \
  "consent_granted:true" \
  "trace_present:true" \
  "human_approved:false"
jq -e '.status == "BLOCK" and .export_allowed == false' "$work_dir/audit-block.json" >/dev/null

run_tool "$work_dir/audit-pass.json" mcp-campusmatch.audit_export \
  "task_id:${task_id}" \
  "idempotency_key:${task_id}-audit-pass-v1" \
  "consent_granted:true" \
  "trace_present:true" \
  "human_approved:true"
jq -e '.status == "PASS" and .export_allowed == true' "$work_dir/audit-pass.json" >/dev/null

run_tool "$work_dir/status.json" mcp-campusmatch.get_task_status \
  "task_id:${task_id}"
jq -e '.status == "READY" and (.completed_stages | length == 5)' "$work_dir/status.json" >/dev/null

jq -n \
  --arg task_id "$task_id" \
  --argjson score "$(jq '.match_score' "$work_dir/match.json")" \
  --argjson coverage "$(jq '.evidence_coverage' "$work_dir/match.json")" \
  --arg audit_block "$(jq -r '.status' "$work_dir/audit-block.json")" \
  --arg audit_pass "$(jq -r '.status' "$work_dir/audit-pass.json")" \
  --arg final_status "$(jq -r '.status' "$work_dir/status.json")" \
  '{task_id:$task_id, profile:"PASS", job:"PASS", match_score:$score, evidence_coverage:$coverage, audit_gate:[$audit_block,$audit_pass], final_status:$final_status}'
