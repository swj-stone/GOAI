#!/usr/bin/env bash
set -euo pipefail

worker_name="${1:?worker name is required}"
gateway_key="${AGENTTEAMS_WORKER_GATEWAY_KEY:-}"

if [[ -z "$gateway_key" ]]; then
  echo "Worker gateway credential is unavailable." >&2
  exit 1
fi

agent_dir="/root/agentteams-fs/agents/${worker_name}"
config_dir="${agent_dir}/config"
config_file="${config_dir}/mcporter.json"
compat_file="${agent_dir}/mcporter-servers.json"
temp_file="${config_file}.tmp"
server_name="mcp-campusmatch"
server_url="http://aigw-local.agentteams.io:8080/mcp-servers/${server_name}/mcp"

mkdir -p "$config_dir"

if [[ -s "$config_file" ]] && jq -e '.mcpServers | type == "object"' "$config_file" >/dev/null 2>&1; then
  jq \
    --arg name "$server_name" \
    --arg url "$server_url" \
    --arg key "$gateway_key" \
    '.mcpServers[$name] = {
      url: $url,
      transport: "http",
      headers: {Authorization: ("Bearer " + $key)}
    }' "$config_file" > "$temp_file"
else
  jq -n \
    --arg name "$server_name" \
    --arg url "$server_url" \
    --arg key "$gateway_key" \
    '{mcpServers: {($name): {
      url: $url,
      transport: "http",
      headers: {Authorization: ("Bearer " + $key)}
    }}}' > "$temp_file"
fi

jq -e --arg name "$server_name" '.mcpServers[$name].headers.Authorization | startswith("Bearer ")' "$temp_file" >/dev/null
mv "$temp_file" "$config_file"
ln -sfn "config/mcporter.json" "$compat_file"

echo "Configured ${server_name} for ${worker_name}."
