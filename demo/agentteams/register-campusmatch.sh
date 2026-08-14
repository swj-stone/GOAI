#!/usr/bin/env bash
set -euo pipefail

# HiClaw's packaged setup script assumes the Manager and Higress console share
# localhost. In this Docker deployment the console runs in the Controller
# container, so create a temporary patched copy while preserving the official
# registration workflow.
export HIGRESS_CONSOLE_URL="http://agentteams-controller:8001"
source /opt/agentteams/scripts/lib/gateway-api.sh
gateway_ensure_session

official_script="/opt/agentteams/agent/skills/mcp-server-management/scripts/setup-mcp-server.sh"
patched_script="/tmp/setup-mcp-server-campusmatch.sh"

sed 's#CONSOLE_URL="http://127\.0\.0\.1:8001"#CONSOLE_URL="http://agentteams-controller:8001"#' \
  "$official_script" > "$patched_script"

grep -q 'CONSOLE_URL="http://agentteams-controller:8001"' "$patched_script"
exec bash "$patched_script" "$@"
