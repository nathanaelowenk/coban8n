#!/usr/bin/env bash
set -euo pipefail

API_URL=${1:-http://localhost:5000/api/report}

echo "Posting sample bug report to ${API_URL}" >&2
curl -sS -X POST "${API_URL}" \
  -H "Content-Type: application/json" \
  -d @"$(dirname "$0")/sample_bug.json" | jq '.'
