# Network Monitoring System - Requirements

Last updated: 2025-01-15
Version: 1.2.0

## Purpose

Build a comprehensive network and system monitoring platform that:
1. Tracks host availability via heartbeat monitoring
2. Analyzes system logs using LLM-powered analysis
3. Monitors internet connectivity
4. Sends alerts via Discord webhooks

## Technology Selections

### Backend
- **Language**: Python 3.11+
- **Web Framework**: FastAPI
- **Database**: SQLite (with future PostgreSQL support)
- **Deployment**: Docker + Docker Compose

### Key Libraries
- **FastAPI**: Web API framework
- **SQLAlchemy**: ORM for database operations
- **APScheduler**: Background job scheduling
- **Paramiko**: SSH client for remote log access
- **Requests**: HTTP client for webhooks and APIs
- **Pydantic**: Data validation and settings management
- **PyYAML**: Configuration file parsing

### External Services
- **Discord**: Webhook-based notifications
- **Healthchecks.io**: Internet connectivity monitoring
- **Unified LLM API**: Log analysis (supports Claude Sonnet 4.5, ChatGPT 5, GLM 4.6)

## Functional Requirements

### FR1: Heartbeat Monitoring
**Priority**: Critical

**Description**: Hosts call unique URLs at configured intervals to signal they are operational.

**Requirements**:
- Each host has a unique identifier and authentication token
- Configurable heartbeat frequency per host (e.g., every 5 minutes, every hour)
- Grace period before alerting on missed heartbeat
- Support for different monitoring schedules:
  - `always`: 24/7 monitoring
  - `business_hours`: 8am-6pm Mon-Fri (configurable timezone)
  - `custom`: Custom cron-like schedules
- Track last seen timestamp for each host
- REST API endpoint: `POST|GET /api/v1/heartbeat/{host_id}` (v1.2.0: Both methods supported)
- Token-based authentication with two methods:
  - **Query parameter**: `?token=xxx` (v1.2.0: Recommended - single complete URL)
  - **Bearer header**: `Authorization: Bearer xxx` (v1.0: Backward compatible)
- **Schedule-aware monitoring logic** (v1.2.0):
  - For business hours: if last heartbeat before window start, calculate from window start
  - Prevents false alerts at monitoring window start times
  - Example: 8am window start won't alert at 8:01am if last heartbeat was yesterday

**Acceptance Criteria**:
- Host can send heartbeat via simple HTTP GET or POST
- URL works in browser (paste and go)
- Token embedded in URL for easy client setup
- System correctly identifies missing heartbeats
- Business hours schedule properly suspends/resumes monitoring
- Alert triggered when heartbeat missed beyond grace period
- No false alerts at window start (schedule-aware logic)

### FR2: Discord Alert System
**Priority**: Critical

**Description**: Send notifications to Discord webhook when issues are detected.

**Requirements**:
- Discord webhook integration for all alert types
- Alert categories:
  - Missing heartbeat
  - Log analysis findings
  - Internet connectivity issues
  - System errors
- Rich embed formatting with severity colors
- Alert deduplication to prevent spam
- Configurable alert thresholds

**Acceptance Criteria**:
- Discord message received within 1 minute of alert condition
- Messages include relevant context (host, timestamp, details)
- No duplicate alerts for same issue within cooldown period
- Different severity levels visually distinguished

### FR3: Log Analysis with LLM
**Priority**: High

**Description**: Automatically retrieve and analyze logs from remote systems using LLM.

**Requirements**:
- SSH-based log retrieval from remote hosts
- Configurable log sources (file paths, commands)
- Integration with unified LLM API
- Support for multiple LLM models:
  - Claude Sonnet 4.5
  - ChatGPT 5 Codex
  - GLM 4.6
- Customizable analysis prompts per host
- Structured output parsing (JSON preferred)
- Store analysis results in database
- Alert on critical findings
- Fallback to syslog forwarding if SSH unavailable

**Acceptance Criteria**:
- Successfully SSH to firewall and retrieve logs
- Logs sent to LLM with appropriate prompt
- LLM findings parsed and stored
- Critical findings trigger Discord alerts
- Analysis runs on configured schedule

### FR4: Internet Connectivity Monitor
**Priority**: High

**Description**: Monitor internet connectivity and report status to healthchecks.io.

**Requirements**:
- Periodic connectivity checks:
  - DNS resolution (8.8.8.8, 1.1.1.1)
  - HTTP requests to known endpoints
  - Optional: Gateway ping
- Healthchecks.io integration:
  - Ping healthchecks.io URL on successful check
  - Healthchecks.io sends Discord alert if ping missed
- Configurable check frequency (default: every 5 minutes)
- Local alerting for connectivity issues

**Acceptance Criteria**:
- Successfully pings healthchecks.io on schedule
- Detects internet outages within check interval
- Healthchecks.io triggers alert when pings stop
- System recovers and resumes pinging after outage

### FR5: Host Management API
**Priority**: Medium

**Description**: REST API for managing monitored hosts.

**Requirements**:
- CRUD operations for hosts:
  - `GET /api/v1/hosts` - List all hosts
  - `GET /api/v1/hosts/{host_id}` - Get host details
  - `POST /api/v1/hosts` - Register new host
  - `PUT /api/v1/hosts/{host_id}` - Update host config
  - `DELETE /api/v1/hosts/{host_id}` - Remove host
- API key authentication for management endpoints
- Input validation and error handling
- Host status summary (up/down/unknown)

**Acceptance Criteria**:
- All CRUD operations work correctly
- Unauthorized requests rejected
- Invalid input returns appropriate error messages
- Host status accurately reflects monitoring state

### FR6: Web Dashboard
**Priority**: High (v1.2.0)

**Description**: Simple web interface showing monitoring status.

**Requirements**:
- Single-page dashboard at `/api/v1/dashboard`
- Display all hosts with current status
- Show last seen timestamp
- Color-coded status indicators
- Recent alerts list
- **Copy buttons for heartbeat URLs** (v1.2.0):
  - One-click copy to clipboard
  - Visual feedback on copy success
  - URLs include embedded tokens
  - Handles special characters correctly
- No authentication required for MVP (view-only)

**Acceptance Criteria**:
- Dashboard loads and displays all hosts
- Status updates reflect real-time data
- Responsive design (mobile-friendly)
- Auto-refresh every 30 seconds
- Copy buttons work reliably with all URL formats
- Visual confirmation when URL copied

### FR7: Configuration Management
**Priority**: Critical

**Description**: Flexible configuration system for hosts and settings.

**Requirements**:
- YAML-based host configuration (`config/hosts.yaml`)
- Environment variable support (`.env` file)
- **Database-backed runtime configuration** (v1.2.0):
  - Webhook URL configurable via UI/API
  - Upstream monitoring settings in database
  - No container restart required for changes
  - Priority: Database > Environment Variables
- Hot-reload configuration changes (where safe)
- Validation of configuration on startup
- Example configurations provided
- **Configuration API endpoints** (v1.2.0):
  - `GET/PUT /api/v1/settings/webhook`
  - `GET/PUT /api/v1/settings/upstream`
  - `GET /api/v1/settings/all`

**Acceptance Criteria**:
- Hosts loaded from YAML file on startup
- Environment variables override defaults
- Invalid configuration causes startup failure with clear error
- Configuration changes applied without full restart (where possible)
- Runtime settings changeable via UI without restart
- Settings API works correctly with validation

### FR8: Upstream Monitoring (Self-Monitoring)
**Priority**: High (v1.2.0)

**Description**: Monitor the monitoring hub itself by sending heartbeats to external services.

**Requirements**:
- Scheduled heartbeat to external monitoring service
- **Configurable via database** (no restart required):
  - Upstream URL (healthchecks.io, Uptime Kuma, etc.)
  - Frequency (default: 5 minutes)
  - Enable/disable toggle
- Support for standard monitoring services:
  - healthchecks.io ping URLs
  - Uptime Kuma push monitors
  - Any HTTP GET endpoint
- **UI configuration page** (`/api/v1/config`):
  - Enable/disable upstream monitoring
  - Set upstream URL
  - Configure frequency
- Logging of successful/failed upstream pings
- Graceful handling of upstream service failures

**Acceptance Criteria**:
- Successfully pings configured upstream service on schedule
- External service alerts if monitoring hub fails
- Can enable/disable via UI without restart
- Can change URL and frequency via UI
- Failed pings logged but don't crash service
- Meta-monitoring: ensures the monitor itself is monitored

## Non-Functional Requirements

### NFR1: Performance
- Heartbeat endpoint response time < 100ms
- Support 20+ hosts without performance degradation
- Database queries optimized with proper indexing
- Background jobs don't block API requests

### NFR2: Reliability
- System uptime > 99.5%
- Graceful handling of external service failures
- Database transactions ensure data consistency
- Automatic retry for transient failures

### NFR3: Security
- All authentication tokens securely stored
- SSH private keys not embedded in Docker images
- Secrets managed via environment variables
- HTTPS for all external API calls
- SQL injection prevention via ORM
- Input validation on all endpoints

### NFR4: Maintainability
- Clean code structure following Python best practices
- Comprehensive logging at appropriate levels
- Type hints throughout codebase
- Documentation for all public interfaces
- Unit tests for critical components

### NFR5: Portability
- Docker-based deployment for consistency
- SQLite default (no external database required)
- Minimal host dependencies
- Configuration via files (easy backup/restore)
- Works on Linux, macOS, Windows (via Docker)

### NFR6: Observability
- Structured logging with log levels
- Request/response logging for API
- Background job execution logging
- Health check endpoint for monitoring
- Database query logging (debug mode)

### NFR7: Scalability (Future)
- Design supports migration to PostgreSQL
- Stateless API design (horizontal scaling ready)
- Background jobs can be distributed
- Database schema supports partitioning

## Data Requirements

### DR1: Data Retention
- Heartbeat history: 30 days
- Alerts: 90 days
- Log analysis results: 60 days
- Configuration: Indefinite
- Automatic cleanup via scheduled job

### DR2: Data Privacy
- No sensitive log content stored in database
- Sanitize logs before LLM analysis
- SSH credentials stored securely
- Discord webhook URL kept confidential

### DR3: Data Backup
- Daily database backup via cron
- Configuration files in version control
- Backup retention: 7 days
- Restore procedure documented

## Integration Requirements

### IR1: Discord
- Webhook URL configurable via environment
- Support for rich embeds
- Respect rate limits
- Graceful handling of webhook failures

### IR2: LLM API
- Support for multiple model endpoints
- API key authentication
- Error handling for rate limits
- Timeout configuration
- Response parsing for JSON and text

### IR3: Healthchecks.io
- Simple HTTP GET to ping URL
- Configurable timeout
- Retry on failure
- Optional: Success/fail pings

### IR4: SSH
- Public key authentication
- Connection pooling/reuse
- Timeout configuration
- Error handling for connection failures
- Command execution logging

## Environment Variables

Required:
- `DISCORD_WEBHOOK_URL`: Discord webhook for alerts
- `LLM_API_KEY`: API key for LLM service
- `LLM_API_URL`: Endpoint for LLM API

Optional:
- `API_HOST`: API bind address (default: 0.0.0.0)
- `API_PORT`: API port (default: 8080)
- `API_SECRET_KEY`: Secret for session management
- `DATABASE_URL`: Database connection string
- `HEALTHCHECKS_URL`: Healthchecks.io ping URL
- `LOG_LEVEL`: Logging level (default: INFO)
- `BUSINESS_HOURS_START`: Start time (default: 08:00)
- `BUSINESS_HOURS_END`: End time (default: 18:00)
- `BUSINESS_HOURS_DAYS`: Active days (default: 1,2,3,4,5)
- `BUSINESS_HOURS_TIMEZONE`: Timezone (default: America/New_York)

## Testing Requirements

### Unit Tests
- Database models and queries
- Schedule utilities (business hours logic)
- Alert deduplication logic
- Configuration parsing

### Integration Tests
- API endpoint responses
- Database operations
- SSH connectivity
- Discord webhook sending

### Manual Testing
- End-to-end heartbeat flow
- Log analysis workflow
- Alert notifications
- Dashboard functionality

## Documentation Requirements

- Architecture diagram (created)
- API endpoint documentation
- Configuration examples
- Setup/installation guide
- Client script examples
- Troubleshooting guide
- Security best practices

## Deployment Requirements

- Docker Compose file for all services
- Dockerfile optimized for size and security
- Volume mounts for data persistence
- Network configuration for service communication
- Health checks for all containers
- Restart policies configured
- Logging to stdout/stderr (Docker logging drivers)

## Success Criteria

**MVP Success** (Phase 1):
1. ✅ 6-20 hosts monitored successfully
2. ✅ Heartbeats received and tracked accurately
3. ✅ Missing heartbeats trigger Discord alerts within 2 minutes
4. ✅ Firewall logs analyzed via SSH + LLM
5. ✅ Critical log findings sent to Discord
6. ✅ Internet connectivity monitored via healthchecks.io
7. ✅ Business hours scheduling works correctly
8. ✅ System runs stably for 7+ days without intervention
9. ✅ Docker Compose deployment works on fresh system
10. ✅ Documentation complete and accurate

**v1.2.0 Success** (Completed):
1. ✅ Schedule-aware monitoring prevents false alerts
2. ✅ Token-embedded URLs simplify client setup
3. ✅ GET/POST method support improves compatibility
4. ✅ Copy buttons enhance UI usability
5. ✅ Runtime configuration system (zero-downtime changes)
6. ✅ Upstream monitoring ensures hub availability
7. ✅ Full backward compatibility maintained
8. ✅ Documentation updated comprehensively

**Phase 2 Success** (Future):
- PostgreSQL migration complete
- Web dashboard with authentication
- Alert acknowledgment workflow
- Historical metrics and graphs
- 50+ hosts monitored

**Phase 3 Success**:
- Multi-region deployment
- Auto-remediation for common issues
- Machine learning anomaly detection
- Integration with Prometheus/Grafana

## Version 1.2.0 Feature Summary

### Core Enhancements

**1. Schedule-Aware Monitoring Logic**
- **Problem Solved**: False alerts at business hours window start
- **Solution**: Window-based threshold calculation for business_hours schedules
- **Impact**: No more 8:01am alerts when window starts at 8:00am

**2. Token-Embedded Heartbeat URLs**
- **Problem Solved**: Complex client configuration (URL + separate token)
- **Solution**: Single complete URL with embedded token: `?token=xxx`
- **Impact**: Copy-paste ready, works in browser, simpler setup

**3. HTTP Method Flexibility**
- **Problem Solved**: POST-only endpoint limited testing/compatibility
- **Solution**: Support both GET and POST methods
- **Impact**: Browser-testable, simpler curl, broader tool compatibility

**4. Web UI Copy Buttons**
- **Problem Solved**: Manual URL copying error-prone
- **Solution**: One-click copy buttons with visual feedback
- **Impact**: Faster, more reliable client setup

**5. Runtime Configuration System**
- **Problem Solved**: Container restart required for config changes
- **Solution**: Database-backed settings with API/UI management
- **Impact**: Zero-downtime configuration changes

**6. Upstream Monitoring Service**
- **Problem Solved**: Monitoring hub itself not monitored
- **Solution**: Scheduled heartbeats to external services (healthchecks.io, Uptime Kuma)
- **Impact**: Meta-monitoring ensures hub availability

### Technical Implementation

**Database Schema Changes**:
- Added `config` table for runtime settings
- Store webhook URL, upstream monitoring config

**API Additions**:
- `GET /api/v1/heartbeat/{host_id}` - Accept GET requests
- `GET/PUT /api/v1/settings/webhook` - Manage webhook URL
- `GET/PUT /api/v1/settings/upstream` - Manage upstream monitoring
- `GET /api/v1/settings/all` - Get all runtime settings

**UI Enhancements**:
- Copy buttons on Dashboard page
- Copy buttons on Config page
- Settings management on Config page
- Data attributes for event handling (special character safety)

**Service Layer**:
- `UpstreamMonitor` service for self-monitoring
- Schedule-aware logic in heartbeat checker
- Settings service for database-backed config

### Backward Compatibility

All v1.2.0 features maintain backward compatibility:
- Bearer header authentication still works
- POST method still works
- Environment variables still override if database settings not present
- Existing clients require no changes

### Migration Path

**From v1.0 to v1.2.0**:
1. Update Docker image/code
2. Restart container (database migration automatic)
3. Optionally migrate to new features:
   - Update client scripts to use token-in-URL format
   - Configure upstream monitoring via UI
   - Set webhook URL via UI instead of .env

**Zero Breaking Changes**: All v1.0 functionality preserved
