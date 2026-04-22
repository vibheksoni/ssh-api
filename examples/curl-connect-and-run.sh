#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8754}"

if [ -z "${SSH_HOST:-}" ] || [ -z "${SSH_USERNAME:-}" ] || [ -z "${SSH_PASSWORD:-}" ]; then
  echo "Set SSH_HOST, SSH_USERNAME, and SSH_PASSWORD before running this example." >&2
  exit 1
fi

SESSION_JSON="$(curl -sS -X POST "$BASE_URL/session/connect" \
  -H "Content-Type: application/json" \
  -d "{
    \"host\": \"$SSH_HOST\",
    \"username\": \"$SSH_USERNAME\",
    \"password\": \"$SSH_PASSWORD\"
  }")"

echo "Connected:"
echo "$SESSION_JSON"

SESSION_ID="$(printf '%s' "$SESSION_JSON" | python -c "import json,sys; print(json.load(sys.stdin)['session_id'])")"

echo
echo "Running hostname:"
curl -sS -X POST "$BASE_URL/command/exec?session_id=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"command":"hostname","timeout":30}'

echo
echo "Disconnecting:"
curl -sS -X POST "$BASE_URL/session/disconnect/$SESSION_ID"
