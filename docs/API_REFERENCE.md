# Network Monitoring System - API Reference

Last updated: 2025-01-15
Version: 1.2.0

## Base URL

```
http://your-monitor-server:8080/api/v1
```

## Authentication

### Heartbeat Endpoints

Heartbeat endpoints use **token-based authentication** with two methods:

**Method 1: Query Parameter** (Recommended in v1.2.0)
```bash
GET /api/v1/heartbeat/{host_id}?token=YOUR_TOKEN
```

**Method 2: Bearer Token Header** (Backward compatible)
```bash
POST /api/v1/heartbeat/{host_id}
Authorization: Bearer YOUR_TOKEN
```

### Management Endpoints

Management endpoints require **API key authentication**:

```bash
GET /api/v1/hosts
X-API-Key: YOUR_API_KEY
```

## Endpoints

---

### Heartbeat Endpoints

#### Receive Heartbeat

**Endpoint**: `GET|POST /api/v1/heartbeat/{host_id}`

**Description**: Receive a heartbeat signal from a monitored host. Supports both GET and POST methods (v1.2.0).

**Path Parameters**:
- `host_id` (string, required): Unique identifier for the host

**Query Parameters**:
- `token` (string, optional): Authentication token (v1.2.0). Can be used instead of Authorization header.

**Headers**:
- `Authorization` (string, optional): Bearer token authentication. Format: `Bearer YOUR_TOKEN`

**Request Examples**:

```bash
# Method 1: GET with token in URL (Recommended)
curl "http://monitor:8080/api/v1/heartbeat/web01?token=abc123xyz"

# Method 2: POST with token in URL
curl -X POST "http://monitor:8080/api/v1/heartbeat/web01?token=abc123xyz"

# Method 3: POST with Bearer token header
curl -X POST http://monitor:8080/api/v1/heartbeat/web01 \
  -H "Authorization: Bearer abc123xyz"

# Method 4: Browser (paste in address bar)
http://monitor:8080/api/v1/heartbeat/web01?token=abc123xyz
```

**Success Response** (200 OK):

```json
{
  "message": "Heartbeat received",
  "host_id": "web01",
  "timestamp": "2025-01-15T14:30:00Z",
  "status": "up"
}
```

**Error Responses**:

404 Not Found - Host not found:
```json
{
  "detail": "Host not found"
}
```

401 Unauthorized - Invalid token:
```json
{
  "detail": "Invalid token"
}
```

---

### Host Management Endpoints

#### List All Hosts

**Endpoint**: `GET /api/v1/hosts`

**Description**: Retrieve a list of all monitored hosts with their current status.

**Query Parameters**:
- `status` (string, optional): Filter by status (`up`, `down`, `unknown`)
- `schedule_type` (string, optional): Filter by schedule type (`always`, `business_hours`, `custom`)

**Request Examples**:

```bash
# Get all hosts
curl http://monitor:8080/api/v1/hosts

# Get only hosts that are down
curl http://monitor:8080/api/v1/hosts?status=down

# Get only 24/7 monitored hosts
curl http://monitor:8080/api/v1/hosts?schedule_type=always
```

**Success Response** (200 OK):

```json
{
  "hosts": [
    {
      "id": 1,
      "name": "web-server-01",
      "host_id": "web01",
      "heartbeat_url": "http://monitor:8080/api/v1/heartbeat/web01?token=abc123xyz",
      "expected_frequency_seconds": 300,
      "grace_period_seconds": 60,
      "schedule_type": "always",
      "schedule_config": null,
      "last_seen": "2025-01-15T14:30:00Z",
      "status": "up",
      "created_at": "2025-01-10T10:00:00Z",
      "updated_at": "2025-01-15T14:30:00Z"
    },
    {
      "id": 2,
      "name": "backup-server",
      "host_id": "backup01",
      "heartbeat_url": "http://monitor:8080/api/v1/heartbeat/backup01?token=xyz789abc",
      "expected_frequency_seconds": 3600,
      "grace_period_seconds": 300,
      "schedule_type": "business_hours",
      "schedule_config": {
        "start": "08:00",
        "end": "18:00",
        "days": [1, 2, 3, 4, 5],
        "timezone": "America/Chicago"
      },
      "last_seen": "2025-01-15T09:00:00Z",
      "status": "up",
      "created_at": "2025-01-12T08:00:00Z",
      "updated_at": "2025-01-15T09:00:00Z"
    }
  ],
  "total": 2
}
```

---

#### Get Host Details

**Endpoint**: `GET /api/v1/hosts/{host_id}`

**Description**: Retrieve detailed information about a specific host.

**Path Parameters**:
- `host_id` (string, required): Unique identifier for the host

**Request Example**:

```bash
curl http://monitor:8080/api/v1/hosts/web01
```

**Success Response** (200 OK):

```json
{
  "id": 1,
  "name": "web-server-01",
  "host_id": "web01",
  "heartbeat_url": "http://monitor:8080/api/v1/heartbeat/web01?token=abc123xyz",
  "token": "abc123xyz",
  "expected_frequency_seconds": 300,
  "grace_period_seconds": 60,
  "schedule_type": "always",
  "schedule_config": null,
  "last_seen": "2025-01-15T14:30:00Z",
  "status": "up",
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-15T14:30:00Z",
  "recent_heartbeats": [
    {
      "timestamp": "2025-01-15T14:30:00Z",
      "source_ip": "192.168.1.100"
    },
    {
      "timestamp": "2025-01-15T14:25:00Z",
      "source_ip": "192.168.1.100"
    }
  ]
}
```

**Error Response** (404 Not Found):

```json
{
  "detail": "Host not found"
}
```

---

#### Create New Host

**Endpoint**: `POST /api/v1/hosts`

**Description**: Register a new host for monitoring.

**Request Body**:

```json
{
  "name": "web-server-01",
  "expected_frequency_seconds": 300,
  "grace_period_seconds": 60,
  "schedule_type": "always",
  "schedule_config": null
}
```

**Request Body Fields**:
- `name` (string, required): Human-readable name for the host
- `expected_frequency_seconds` (integer, required): Expected time between heartbeats in seconds
- `grace_period_seconds` (integer, optional, default: 60): Grace period before alerting
- `schedule_type` (string, optional, default: "always"): Monitoring schedule type
  - `always`: 24/7 monitoring
  - `business_hours`: Only during business hours
  - `custom`: Custom schedule (requires schedule_config)
- `schedule_config` (object, optional): Custom schedule configuration

**Request Example**:

```bash
curl -X POST http://monitor:8080/api/v1/hosts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-server-01",
    "expected_frequency_seconds": 300,
    "grace_period_seconds": 60,
    "schedule_type": "always"
  }'
```

**Success Response** (201 Created):

```json
{
  "id": 1,
  "name": "web-server-01",
  "host_id": "web-server-01",
  "heartbeat_url": "http://monitor:8080/api/v1/heartbeat/web-server-01?token=abc123xyz",
  "token": "abc123xyz",
  "expected_frequency_seconds": 300,
  "grace_period_seconds": 60,
  "schedule_type": "always",
  "schedule_config": null,
  "last_seen": null,
  "status": "unknown",
  "created_at": "2025-01-15T14:30:00Z",
  "updated_at": "2025-01-15T14:30:00Z"
}
```

**Error Responses**:

400 Bad Request - Validation error:
```json
{
  "detail": "Validation error",
  "errors": [
    {
      "field": "expected_frequency_seconds",
      "message": "Must be greater than 0"
    }
  ]
}
```

409 Conflict - Host already exists:
```json
{
  "detail": "Host with this name already exists"
}
```

---

#### Update Host

**Endpoint**: `PUT /api/v1/hosts/{host_id}`

**Description**: Update configuration for an existing host.

**Path Parameters**:
- `host_id` (string, required): Unique identifier for the host

**Request Body**: Same as Create Host, but all fields are optional.

```json
{
  "expected_frequency_seconds": 600,
  "schedule_type": "business_hours"
}
```

**Request Example**:

```bash
curl -X PUT http://monitor:8080/api/v1/hosts/web01 \
  -H "Content-Type: application/json" \
  -d '{
    "expected_frequency_seconds": 600,
    "schedule_type": "business_hours"
  }'
```

**Success Response** (200 OK):

```json
{
  "id": 1,
  "name": "web-server-01",
  "host_id": "web01",
  "heartbeat_url": "http://monitor:8080/api/v1/heartbeat/web01?token=abc123xyz",
  "expected_frequency_seconds": 600,
  "grace_period_seconds": 60,
  "schedule_type": "business_hours",
  "schedule_config": null,
  "last_seen": "2025-01-15T14:30:00Z",
  "status": "up",
  "updated_at": "2025-01-15T14:35:00Z"
}
```

---

#### Delete Host

**Endpoint**: `DELETE /api/v1/hosts/{host_id}`

**Description**: Remove a host from monitoring.

**Path Parameters**:
- `host_id` (string, required): Unique identifier for the host

**Request Example**:

```bash
curl -X DELETE http://monitor:8080/api/v1/hosts/web01
```

**Success Response** (204 No Content):

No response body.

**Error Response** (404 Not Found):

```json
{
  "detail": "Host not found"
}
```

---

### Settings Endpoints (v1.2.0)

#### Get All Settings

**Endpoint**: `GET /api/v1/settings/all`

**Description**: Retrieve all runtime configuration settings.

**Request Example**:

```bash
curl http://monitor:8080/api/v1/settings/all
```

**Success Response** (200 OK):

```json
{
  "webhook": {
    "url": "https://discord.com/api/webhooks/123456/abcdef",
    "source": "database",
    "updated_at": "2025-01-15T10:00:00Z"
  },
  "upstream": {
    "enabled": true,
    "url": "https://hc-ping.com/your-uuid",
    "frequency_seconds": 300,
    "source": "database",
    "updated_at": "2025-01-15T10:05:00Z"
  }
}
```

---

#### Get Webhook Settings

**Endpoint**: `GET /api/v1/settings/webhook`

**Description**: Get current Discord webhook URL.

**Request Example**:

```bash
curl http://monitor:8080/api/v1/settings/webhook
```

**Success Response** (200 OK):

```json
{
  "webhook_url": "https://discord.com/api/webhooks/123456/abcdef",
  "source": "database"
}
```

---

#### Update Webhook Settings

**Endpoint**: `PUT /api/v1/settings/webhook`

**Description**: Update Discord webhook URL at runtime (no restart required).

**Request Body**:

```json
{
  "webhook_url": "https://discord.com/api/webhooks/NEW_ID/NEW_TOKEN"
}
```

**Request Example**:

```bash
curl -X PUT http://monitor:8080/api/v1/settings/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://discord.com/api/webhooks/789012/ghijkl"
  }'
```

**Success Response** (200 OK):

```json
{
  "message": "Webhook URL updated successfully",
  "webhook_url": "https://discord.com/api/webhooks/789012/ghijkl"
}
```

**Error Response** (400 Bad Request):

```json
{
  "detail": "Invalid webhook URL format"
}
```

---

#### Get Upstream Monitoring Settings

**Endpoint**: `GET /api/v1/settings/upstream`

**Description**: Get current upstream monitoring configuration.

**Request Example**:

```bash
curl http://monitor:8080/api/v1/settings/upstream
```

**Success Response** (200 OK):

```json
{
  "enabled": true,
  "url": "https://hc-ping.com/your-uuid",
  "frequency_seconds": 300,
  "source": "database"
}
```

---

#### Update Upstream Monitoring Settings

**Endpoint**: `PUT /api/v1/settings/upstream`

**Description**: Configure upstream monitoring (self-monitoring) at runtime.

**Request Body**:

```json
{
  "enabled": true,
  "url": "https://hc-ping.com/your-uuid",
  "frequency_seconds": 300
}
```

**Request Body Fields**:
- `enabled` (boolean, required): Enable or disable upstream monitoring
- `url` (string, optional): Upstream service URL (healthchecks.io, Uptime Kuma, etc.)
- `frequency_seconds` (integer, optional): How often to ping upstream (default: 300)

**Request Example**:

```bash
curl -X PUT http://monitor:8080/api/v1/settings/upstream \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "url": "https://hc-ping.com/abc-123-xyz",
    "frequency_seconds": 300
  }'
```

**Success Response** (200 OK):

```json
{
  "message": "Upstream monitoring settings updated successfully",
  "enabled": true,
  "url": "https://hc-ping.com/abc-123-xyz",
  "frequency_seconds": 300
}
```

**Error Response** (400 Bad Request):

```json
{
  "detail": "URL is required when enabled is true"
}
```

---

### Web UI Endpoints

#### Dashboard

**Endpoint**: `GET /api/v1/dashboard`

**Description**: Web-based dashboard showing all hosts and their status.

**Access**: Open in browser at `http://monitor:8080/api/v1/dashboard`

**Features**:
- Real-time host status display
- Color-coded status indicators (green=up, red=down, gray=unknown)
- Last seen timestamps
- Copy buttons for heartbeat URLs (v1.2.0)
- Auto-refresh every 30 seconds
- Responsive mobile-friendly design

**Response**: HTML page

---

#### Configuration UI

**Endpoint**: `GET /api/v1/config`

**Description**: Web-based configuration interface.

**Access**: Open in browser at `http://monitor:8080/api/v1/config`

**Features**:
- Add/edit/delete hosts
- Configure Discord webhook URL (v1.2.0)
- Configure upstream monitoring (v1.2.0)
- Copy buttons for heartbeat URLs (v1.2.0)
- Real-time validation
- No restart required for settings changes (v1.2.0)

**Response**: HTML page

---

### System Endpoints

#### Health Check

**Endpoint**: `GET /api/v1/health`

**Description**: Check system health and status.

**Request Example**:

```bash
curl http://monitor:8080/api/v1/health
```

**Success Response** (200 OK):

```json
{
  "status": "healthy",
  "version": "1.2.0",
  "uptime_seconds": 86400,
  "database": "connected",
  "scheduler": "running",
  "components": {
    "api": "healthy",
    "database": "healthy",
    "scheduler": "healthy",
    "upstream_monitor": "enabled"
  },
  "timestamp": "2025-01-15T14:30:00Z"
}
```

**Degraded Response** (200 OK):

```json
{
  "status": "degraded",
  "version": "1.2.0",
  "uptime_seconds": 86400,
  "database": "connected",
  "scheduler": "error",
  "components": {
    "api": "healthy",
    "database": "healthy",
    "scheduler": "error",
    "upstream_monitor": "error"
  },
  "errors": [
    "Scheduler job 'heartbeat_checker' failed"
  ],
  "timestamp": "2025-01-15T14:30:00Z"
}
```

---

## Response Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Delete successful |
| 400 | Bad Request | Invalid request body or parameters |
| 401 | Unauthorized | Authentication failed |
| 404 | Not Found | Resource not found |
| 405 | Method Not Allowed | HTTP method not supported (v1.0 only, fixed in v1.2.0) |
| 409 | Conflict | Resource already exists |
| 500 | Internal Server Error | Server error |

---

## Rate Limiting

**Current Implementation**: No rate limiting enforced.

**Best Practices**:
- Heartbeat endpoints: Respect your configured frequency
- Management endpoints: Reasonable usage (< 100 requests/minute)

**Future**: Rate limiting may be added in v2.0.

---

## Pagination

**Current Implementation**: No pagination.

**Response Limits**:
- `/api/v1/hosts`: Returns all hosts
- Host details: Includes last 10 heartbeats

**Future**: Pagination will be added when scale requires it.

---

## Webhooks (Outgoing)

### Discord Webhook Format

The system sends alerts to Discord using webhook embeds:

**Alert Structure**:

```json
{
  "embeds": [
    {
      "title": "🚨 Alert: Host Down",
      "description": "Host 'web-server-01' has missed its heartbeat",
      "color": 15158332,
      "fields": [
        {
          "name": "Host",
          "value": "web-server-01",
          "inline": true
        },
        {
          "name": "Last Seen",
          "value": "2025-01-15 14:30:00 UTC",
          "inline": true
        },
        {
          "name": "Expected Every",
          "value": "5 minutes",
          "inline": true
        },
        {
          "name": "Grace Period",
          "value": "60 seconds",
          "inline": true
        }
      ],
      "timestamp": "2025-01-15T14:36:00Z",
      "footer": {
        "text": "Network Monitoring System v1.2.0"
      }
    }
  ]
}
```

**Alert Colors**:
- 🔴 Red (`15158332`): Critical - Host down
- 🟡 Yellow (`16776960`): Warning - Degraded
- 🟢 Green (`3066993`): Info/Recovery
- ⚪ Gray (`9807270`): Unknown/System

---

## SDKs and Client Libraries

### Python Client Example

```python
import requests
from typing import Optional

class MonitoringClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers['X-API-Key'] = api_key

    def send_heartbeat(self, host_id: str, token: str) -> bool:
        """Send heartbeat for a host"""
        url = f"{self.base_url}/api/v1/heartbeat/{host_id}?token={token}"
        try:
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Heartbeat failed: {e}")
            return False

    def get_hosts(self, status: Optional[str] = None):
        """Get all hosts, optionally filtered by status"""
        url = f"{self.base_url}/api/v1/hosts"
        params = {}
        if status:
            params['status'] = status

        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def create_host(self, name: str, frequency: int, **kwargs):
        """Create a new host"""
        url = f"{self.base_url}/api/v1/hosts"
        data = {
            "name": name,
            "expected_frequency_seconds": frequency,
            **kwargs
        }
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

# Usage
client = MonitoringClient("http://monitor:8080")
client.send_heartbeat("web01", "abc123xyz")
```

### Bash Client Example

```bash
#!/bin/bash
# monitoring_client.sh

MONITOR_URL="http://monitor:8080/api/v1"
API_KEY="your-api-key"

# Send heartbeat
send_heartbeat() {
    local host_id=$1
    local token=$2
    curl -sf "${MONITOR_URL}/heartbeat/${host_id}?token=${token}"
}

# Get all hosts
get_hosts() {
    curl -sf "${MONITOR_URL}/hosts" \
        -H "X-API-Key: ${API_KEY}" | jq
}

# Create host
create_host() {
    local name=$1
    local frequency=$2

    curl -sf "${MONITOR_URL}/hosts" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: ${API_KEY}" \
        -d "{
            \"name\": \"${name}\",
            \"expected_frequency_seconds\": ${frequency}
        }" | jq
}

# Usage
send_heartbeat "web01" "abc123xyz"
```

---

## Changelog

### v1.2.0 (2025-01-15)

**New Endpoints**:
- `GET /api/v1/heartbeat/{host_id}` - Added GET method support
- `GET /api/v1/settings/all` - Get all runtime settings
- `GET /api/v1/settings/webhook` - Get webhook configuration
- `PUT /api/v1/settings/webhook` - Update webhook configuration
- `GET /api/v1/settings/upstream` - Get upstream monitoring configuration
- `PUT /api/v1/settings/upstream` - Update upstream monitoring configuration

**Enhancements**:
- Token authentication via query parameter (`?token=xxx`)
- Schedule-aware monitoring logic (prevents false alerts)
- Copy buttons in Dashboard and Config UI
- Runtime configuration (zero-downtime changes)
- Upstream monitoring service (self-monitoring)

**Backward Compatibility**:
- All v1.0 features preserved
- Bearer token authentication still supported
- POST method still works for heartbeats

### v1.0.0 (2025-01-10)

**Initial Release**:
- Heartbeat monitoring (POST only)
- Host management API
- Discord alerting
- Business hours scheduling
- Dashboard UI
- Health check endpoint

---

## Support

**Documentation**:
- [Architecture](./ARCHITECTURE.md)
- [Requirements](./REQUIREMENTS.md)
- [Usage Examples](./USAGE_EXAMPLES.md)
- [README](../README.md)

**Issues**: Report via your organization's issue tracking system

**Questions**: Contact the monitoring team
