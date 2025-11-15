#!/bin/bash
# Client-side heartbeat script
# Send heartbeat to monitoring server
#
# Usage:
#   ./client-heartbeat.sh <host_id> <token> <server_url>
#
# Example:
#   ./client-heartbeat.sh web01 abc123token http://monitor.example.com:8080
#
# Setup as cron job (every 5 minutes):
#   */5 * * * * /path/to/client-heartbeat.sh web01 abc123token http://monitor.example.com:8080

set -e

# Configuration
HOST_ID="${1:-}"
TOKEN="${2:-}"
SERVER_URL="${3:-http://localhost:8080}"

# Validation
if [ -z "$HOST_ID" ] || [ -z "$TOKEN" ]; then
    echo "Error: Missing required arguments"
    echo "Usage: $0 <host_id> <token> [server_url]"
    exit 1
fi

# Build heartbeat URL
HEARTBEAT_URL="${SERVER_URL}/api/v1/heartbeat/${HOST_ID}"

# Send heartbeat
RESPONSE=$(curl -s -X POST "${HEARTBEAT_URL}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -w "\nHTTP_STATUS:%{http_code}" \
    2>&1)

# Extract HTTP status
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)

# Check result
if [ "$HTTP_STATUS" = "200" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Heartbeat sent successfully for ${HOST_ID}"
    exit 0
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Failed to send heartbeat for ${HOST_ID}"
    echo "Response: $RESPONSE"
    exit 1
fi
