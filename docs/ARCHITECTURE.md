# Network Monitoring System - Architecture

Last updated: 2025-11-15

## Overview

A Python-based network and system monitoring platform deployed via Docker Compose. Provides heartbeat monitoring, LLM-powered log analysis, and internet connectivity tracking with Discord alerting.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Network Monitoring System                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  FastAPI Server  │  │  Log Analyzer    │  │   Internet    │ │
│  │  (Heartbeat API) │  │  (SSH + LLM)     │  │   Monitor     │ │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘ │
│           │                     │                     │          │
│  ┌────────▼─────────────────────▼─────────────────────▼───────┐ │
│  │              Alert Service (Discord Webhook)               │ │
│  └────────────────────────────┬───────────────────────────────┘ │
│                               │                                  │
│  ┌────────────────────────────▼───────────────────────────────┐ │
│  │           SQLite Database (Configuration + State)          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           APScheduler (Background Jobs)                     │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────┐
        │  External Services                        │
        │  - Discord (Webhooks)                     │
        │  - Healthchecks.io (Internet monitoring)  │
        │  - Unified LLM API (Log analysis)         │
        │  - Monitored Hosts (SSH, Heartbeats)      │
        └──────────────────────────────────────────┘
```

## Core Components

### 1. Heartbeat Monitoring API (FastAPI)
**Purpose**: Receive and track periodic heartbeat signals from monitored hosts

**Endpoints**:
- `POST /api/v1/heartbeat/{host_id}` - Receive heartbeat ping
- `GET /api/v1/hosts` - List all monitored hosts and status
- `GET /api/v1/hosts/{host_id}` - Get specific host details
- `POST /api/v1/hosts` - Register new host
- `GET /api/v1/dashboard` - Web dashboard (HTML)
- `GET /api/v1/health` - System health check

**Features**:
- Token-based authentication for heartbeats
- Configurable expected frequency per host
- Schedule-aware monitoring (24/7 vs business hours)
- Grace period before alerting
- Last seen timestamp tracking

### 2. Alert Service
**Purpose**: Send notifications via Discord webhook

**Features**:
- Discord webhook integration
- Alert deduplication (prevent spam)
- Alert acknowledgment tracking
- Multiple alert types:
  - Missing heartbeat
  - Log analysis findings
  - Internet connectivity issues
  - System errors

**Alert Format**:
```json
{
  "embeds": [{
    "title": "Alert: Host Down",
    "description": "Host 'web-server-01' missed heartbeat",
    "color": 15158332,
    "fields": [
      {"name": "Host", "value": "web-server-01"},
      {"name": "Last Seen", "value": "2025-11-15 10:30:00"},
      {"name": "Expected Every", "value": "5 minutes"}
    ],
    "timestamp": "2025-11-15T10:35:00"
  }]
}
```

### 3. Log Analyzer Service
**Purpose**: SSH to remote hosts, retrieve logs, and analyze with LLM

**Components**:
- **SSH Client**: Paramiko-based SSH connection
- **Log Retrieval**: Fetch logs since last check or last N lines
- **LLM Integration**: Send logs to unified API for analysis
- **Finding Parser**: Extract and categorize LLM findings
- **Alert Generator**: Send significant findings to Discord

**Workflow**:
1. SSH to configured host (e.g., firewall)
2. Execute log retrieval command (e.g., `tail -n 1000 /var/log/firewall.log`)
3. Send logs to LLM with analysis prompt
4. Parse LLM response for security issues/anomalies
5. Store findings in database
6. Alert if critical issues found

**Fallback**: Syslog forwarding if SSH not feasible

### 4. Internet Monitor
**Purpose**: Track internet connectivity and report to healthchecks.io

**Checks**:
- DNS resolution (8.8.8.8, 1.1.1.1)
- HTTP connectivity to known endpoints
- Ping to gateway
- Optional: Speedtest integration

**Healthchecks.io Integration**:
- Successful checks ping healthchecks.io URL
- Failed pings trigger healthchecks.io -> Discord alert
- Configurable check frequency

### 5. Scheduler (APScheduler)
**Purpose**: Run background tasks on defined schedules

**Jobs**:
- **Heartbeat Checker**: Every 1 minute, check for missing heartbeats
- **Log Analyzer**: Configurable per host (e.g., every 30 minutes)
- **Internet Monitor**: Every 5 minutes
- **Database Cleanup**: Daily, remove old records
- **Health Check**: Hourly, verify system components

### 6. Database (SQLite)
**Schema**:

```sql
-- Host configuration
CREATE TABLE hosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    host_id TEXT UNIQUE NOT NULL,
    heartbeat_url TEXT,
    token TEXT,
    expected_frequency_seconds INTEGER NOT NULL,
    schedule_type TEXT DEFAULT 'always', -- 'always', 'business_hours', 'custom'
    schedule_config TEXT, -- JSON for custom schedules
    grace_period_seconds INTEGER DEFAULT 60,
    last_seen TIMESTAMP,
    status TEXT DEFAULT 'unknown', -- 'up', 'down', 'unknown'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Heartbeat log
CREATE TABLE heartbeats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER REFERENCES hosts(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_ip TEXT,
    metadata TEXT -- JSON for additional data
);

-- Alerts
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER REFERENCES hosts(id),
    alert_type TEXT NOT NULL, -- 'heartbeat', 'log_analysis', 'internet', 'system'
    severity TEXT DEFAULT 'warning', -- 'info', 'warning', 'critical'
    message TEXT NOT NULL,
    details TEXT, -- JSON
    acknowledged BOOLEAN DEFAULT 0,
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log analysis results
CREATE TABLE log_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER REFERENCES hosts(id),
    log_source TEXT NOT NULL,
    lines_analyzed INTEGER,
    llm_model TEXT,
    findings TEXT, -- JSON array of findings
    severity TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System configuration
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Technology Stack

### Backend
- **Python 3.11+**: Core language
- **FastAPI**: Web framework for API endpoints
- **Uvicorn**: ASGI server
- **SQLAlchemy**: ORM for database
- **APScheduler**: Background job scheduling
- **Paramiko**: SSH client for log retrieval
- **Requests**: HTTP client for LLM API and webhooks
- **Pydantic**: Data validation

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **SQLite**: Database (volume-mounted)

### External Services
- **Discord**: Webhook-based alerting
- **Healthchecks.io**: Internet monitoring
- **Unified LLM API**: Log analysis (Claude Sonnet 4.5, ChatGPT 5, GLM 4.6)

## Deployment Architecture

### Docker Compose Services

```yaml
services:
  api:
    # FastAPI server for heartbeat endpoints and dashboard
    # Ports: 8080:8080
    # Volumes: ./data/db.sqlite, ./config

  scheduler:
    # Background job runner (APScheduler)
    # Shares database with API
    # Volumes: ./data/db.sqlite, ./config

  log-analyzer:
    # Periodic log analysis via SSH + LLM
    # Volumes: ./data/db.sqlite, ./config, ~/.ssh (for keys)

  internet-monitor:
    # Connectivity checks and healthchecks.io integration
    # Volumes: ./data/db.sqlite, ./config
```

### Directory Structure

```
network-monitoring/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .env (gitignored)
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── heartbeat.py      # Heartbeat endpoints
│   │   │   ├── hosts.py          # Host management
│   │   │   └── dashboard.py      # Web UI
│   │   └── dependencies.py       # FastAPI dependencies
│   ├── services/
│   │   ├── __init__.py
│   │   ├── alert_service.py      # Discord webhook alerts
│   │   ├── log_analyzer.py       # SSH + LLM log analysis
│   │   ├── internet_monitor.py   # Connectivity checks
│   │   └── scheduler_service.py  # APScheduler jobs
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                 # Database connection
│   │   ├── models.py             # SQLAlchemy models
│   │   └── schemas.py            # Pydantic schemas
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── discord.py            # Discord webhook client
│   │   ├── llm_client.py         # Unified LLM API client
│   │   ├── ssh_client.py         # SSH connection manager
│   │   └── schedule_utils.py     # Business hours logic
│   └── config.py                 # Configuration management
├── config/
│   ├── hosts.yaml                # Host definitions
│   └── settings.yaml             # System settings
├── scripts/
│   ├── setup.sh                  # Initial setup
│   ├── client-heartbeat.sh       # Client-side heartbeat script
│   └── add-host.py               # Register new host
├── data/
│   └── db.sqlite                 # SQLite database (gitignored)
├── logs/
│   └── *.log                     # Application logs (gitignored)
├── tests/
│   ├── test_api.py
│   ├── test_alerts.py
│   └── test_log_analyzer.py
└── docs/
    └── (existing documentation)
```

## Configuration

### Environment Variables (.env)

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8080
API_SECRET_KEY=<random-secret>

# Database
DATABASE_URL=sqlite:///data/db.sqlite

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# LLM API
LLM_API_URL=https://your-unified-api.com/v1/chat
LLM_API_KEY=<your-api-key>
LLM_DEFAULT_MODEL=claude-sonnet-4.5

# Healthchecks.io
HEALTHCHECKS_URL=https://hc-ping.com/<your-uuid>

# Business Hours (default)
BUSINESS_HOURS_START=08:00
BUSINESS_HOURS_END=18:00
BUSINESS_HOURS_DAYS=1,2,3,4,5  # Mon-Fri
BUSINESS_HOURS_TIMEZONE=America/New_York

# Logging
LOG_LEVEL=INFO
```

### Host Configuration (config/hosts.yaml)

```yaml
hosts:
  - name: web-server-01
    host_id: web01
    token: <unique-token>
    expected_frequency: 300  # 5 minutes
    schedule_type: always
    grace_period: 60

  - name: backup-server
    host_id: backup01
    token: <unique-token>
    expected_frequency: 3600  # 1 hour
    schedule_type: business_hours
    grace_period: 300

  - name: firewall
    host_id: fw01
    token: <unique-token>
    expected_frequency: 600  # 10 minutes
    schedule_type: always
    log_analysis:
      enabled: true
      method: ssh
      ssh_host: 192.168.1.1
      ssh_user: admin
      ssh_key_path: /root/.ssh/id_rsa
      log_command: "tail -n 1000 /var/log/firewall.log"
      analysis_frequency: 1800  # 30 minutes
      analysis_prompt: |
        Analyze these firewall logs for:
        1. Security threats or intrusion attempts
        2. Unusual traffic patterns
        3. Failed authentication attempts
        4. Configuration issues
        Provide findings in JSON format with severity levels.
```

## Security Considerations

1. **Authentication**:
   - Heartbeat endpoints require host-specific tokens
   - API management endpoints require API key

2. **SSH Keys**:
   - Private keys stored securely, not in Docker image
   - Volume-mounted from host system

3. **Secrets Management**:
   - All secrets in `.env` file (gitignored)
   - Docker secrets for production deployment

4. **Network Security**:
   - API exposed only on necessary ports
   - SSH connections to internal hosts only
   - HTTPS for external API calls

5. **Data Privacy**:
   - Logs analyzed locally before sending to LLM
   - Sensitive data filtered before LLM analysis
   - Database contains no sensitive log content

## Scalability & Future Enhancements

### Phase 1 (Current)
- Single server deployment
- SQLite database
- Basic monitoring and alerting

### Phase 2 (Future)
- PostgreSQL for better concurrency
- Redis for caching and job queue
- Multiple worker containers
- Web UI with authentication
- Alert acknowledgment via Discord bot
- Historical metrics and dashboards
- Grafana integration

### Phase 3 (Advanced)
- Multi-region deployment
- Distributed monitoring agents
- Machine learning for anomaly detection
- Auto-remediation capabilities
- Integration with other monitoring tools (Prometheus, Nagios)

## Monitoring the Monitor

The system monitors itself:
- Health check endpoint (`/api/v1/health`)
- System checks as a scheduled job
- Internet monitor validates outbound connectivity
- Healthchecks.io monitors the monitor (meta-monitoring)

## Disaster Recovery

- Database backed up daily via cron
- Configuration in version control
- Docker Compose enables quick redeployment
- Snapshot script for checkpointing state
