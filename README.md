# Network Monitoring System

A comprehensive Python-based network and system monitoring platform with heartbeat monitoring, LLM-powered log analysis, and internet connectivity tracking.

## Features

### Core Monitoring
- 🔄 **Heartbeat Monitoring**: Track host availability via unique URLs with embedded tokens
- 📊 **Schedule-Aware Monitoring**: Prevent false alerts with smart window-based checking
- 🤖 **LLM Log Analysis**: Analyze firewall/system logs using AI (Claude, GPT, GLM)
- 🌐 **Internet Monitoring**: Track connectivity with healthchecks.io integration
- 📢 **Discord Alerts**: Rich webhook-based notifications

### Configuration & Management
- ⚙️ **Runtime Configuration**: Update webhook URL and settings without restart
- 🔄 **Upstream Monitoring**: Self-monitoring via healthchecks.io, Uptime Kuma, etc.
- ⏰ **Business Hours Support**: Schedule monitoring windows to prevent off-hours alerts
- 📋 **One-Click Copy**: Copy complete heartbeat URLs with built-in copy buttons
- 🐳 **Single Container Deployment**: Everything runs in one Docker container

### User Interface
- 📊 **Web Dashboard**: Real-time monitoring dashboard with host status
- ⚙️ **Configuration Manager**: View and edit host settings via web UI
- 🔗 **Token-Embedded URLs**: Complete heartbeat URLs ready to use
- ✅ **Visual Feedback**: Copy buttons with instant feedback

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Discord webhook URL
- LLM API access (unified endpoint supporting Claude/GPT/GLM)
- (Optional) Healthchecks.io or Uptime Kuma account for upstream monitoring

### Installation

1. **Clone or navigate to the project directory**

```bash
cd network-monitoring
```

2. **Run the setup script**

```bash
./scripts/setup.sh
```

3. **Configure environment variables**

Edit `.env` and set required values:

```bash
# Required
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK
LLM_API_URL=https://your-api-endpoint.com/v1/chat
LLM_API_KEY=your-api-key

# Optional - Can be configured via web UI
HEALTHCHECKS_URL=https://hc-ping.com/your-uuid
```

4. **Start the system**

```bash
docker-compose up -d
```

5. **Access the dashboards**

- **Status Dashboard**: [http://localhost:8080/api/v1/dashboard](http://localhost:8080/api/v1/dashboard)
- **Configuration Manager**: [http://localhost:8080/api/v1/config](http://localhost:8080/api/v1/config)
- **API Documentation**: [http://localhost:8080/docs](http://localhost:8080/docs)

## Usage

### Registering a Host

#### Option 1: Web UI (Easiest)

1. Visit [http://localhost:8080/api/v1/config](http://localhost:8080/api/v1/config)
2. Click "Add New Host"
3. Fill in the form:
   - **Name**: Display name (e.g., "Web Server 01")
   - **Host ID**: Unique identifier (e.g., "web01")
   - **Token**: Auto-generated or custom
   - **Frequency**: Heartbeat interval (e.g., "*/5 * * * *" for every 5 minutes)
   - **Grace Period**: How long to wait before alerting (seconds)
   - **Schedule**: "always" for 24/7 or "business_hours" for specific windows
4. Click "Add Host"
5. **Copy the heartbeat URL** using the 📋 button

#### Option 2: Command Line

Use the `add-host.py` script to register a new host:

```bash
python scripts/add-host.py \
  --name "Web Server 01" \
  --host-id web01 \
  --cron "*/5 * * * *" \
  --schedule always
```

The script will:
- Generate a secure token
- Register the host with the API
- Display the complete heartbeat URL with token
- Provide setup instructions for the client

### Client Setup

The heartbeat URL is **complete and ready to use** - just copy it from the dashboard or config page!

#### Simple curl Example (Easiest)

```bash
# Just paste the URL from the copy button:
curl "http://your-monitor-server:8080/api/v1/heartbeat/web01?token=YOUR_TOKEN"
```

That's it! The URL contains everything needed.

#### Using the Provided Script

On the host you want to monitor:

1. **Download the heartbeat script**

```bash
curl -O http://your-monitor-server:8080/scripts/client-heartbeat.sh
chmod +x client-heartbeat.sh
```

2. **Test manually**

```bash
./client-heartbeat.sh web01 YOUR_TOKEN http://your-monitor-server:8080
```

3. **Set up cron job** (every 5 minutes)

```bash
crontab -e
```

Add:

```cron
*/5 * * * * /path/to/client-heartbeat.sh web01 YOUR_TOKEN http://your-monitor-server:8080
```

#### Or Use the Complete URL

Even simpler - just use the URL directly:

```bash
crontab -e
```

Add:

```cron
*/5 * * * * curl "http://your-monitor-server:8080/api/v1/heartbeat/web01?token=YOUR_TOKEN"
```

### Managing Host Configurations

You can view and update host configurations in multiple ways:

#### 1. Web Configuration Manager (Easiest)

Visit [http://localhost:8080/api/v1/config](http://localhost:8080/api/v1/config) to:
- View all host configurations in a table
- **Copy heartbeat URLs** with one click using 📋 buttons
- Edit heartbeat frequency, grace period, and schedule
- Add or delete hosts
- See current status and settings at a glance

#### 2. Dashboard View

Visit [http://localhost:8080/api/v1/dashboard](http://localhost:8080/api/v1/dashboard) to:
- See real-time host status
- View summary table with all heartbeat URLs
- **Copy URLs** with 📋 Copy buttons
- Monitor recent alerts
- Track system health

#### 3. API Endpoints

View all configurations:
```bash
curl http://localhost:8080/api/v1/hosts/config/all
```

Update a host's configuration:
```bash
curl -X PATCH "http://localhost:8080/api/v1/hosts/web01/config?frequency_seconds=600&schedule_type=business_hours"
```

Get a specific host with heartbeat URL:
```bash
curl http://localhost:8080/api/v1/hosts/web01
```

#### 4. Programmatically

```python
import requests

# Update frequency to 10 minutes and set business hours schedule
response = requests.patch(
    "http://localhost:8080/api/v1/hosts/web01/config",
    params={
        "frequency_seconds": 600,
        "schedule_type": "business_hours"
    }
)
print(response.json())
```

**Common Configuration Changes:**

- **Change heartbeat frequency**: Adjust how often the host should check in
- **Update grace period**: Set how long to wait before alerting on missed heartbeat
- **Switch schedule**: Toggle between 24/7 monitoring and business hours only
- **Copy heartbeat URL**: Use the copy button to get the complete URL with token

### Configuring Runtime Settings

#### Webhook URL Configuration

You can update the Discord webhook URL without restarting the container:

**Via Web UI**:
1. Visit [http://localhost:8080/api/v1/config](http://localhost:8080/api/v1/config)
2. Scroll to "Notification Settings"
3. Enter your new webhook URL
4. Click "Save Webhook"

**Via API**:
```bash
curl -X PUT http://localhost:8080/api/v1/settings/webhook \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://discord.com/api/webhooks/NEW_URL"}'
```

#### Upstream Monitoring Configuration

Configure the monitoring hub to send heartbeats to an external service (self-monitoring):

**Via Web UI**:
1. Visit [http://localhost:8080/api/v1/config](http://localhost:8080/api/v1/config)
2. Scroll to "Upstream Monitoring (Self-Monitoring)"
3. Enable upstream monitoring
4. Enter your healthchecks.io or Uptime Kuma URL
5. Set frequency (default: 300 seconds)
6. Click "Save Config"

**Via API**:
```bash
curl -X PUT http://localhost:8080/api/v1/settings/upstream \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "url": "https://hc-ping.com/your-uuid",
    "frequency_seconds": 300
  }'
```

This ensures an external service monitors the monitoring hub itself, preventing unknown failures.

### Configuring Log Analysis

To enable log analysis for a host (e.g., firewall):

1. **Edit the host configuration**

Add `log_analysis_config` to your host (via API):

```json
{
  "enabled": true,
  "method": "ssh",
  "ssh_host": "192.168.1.1",
  "ssh_user": "admin",
  "ssh_key_path": "/root/.ssh/id_rsa",
  "log_command": "tail -n 1000 /var/log/firewall.log",
  "analysis_frequency": 1800,
  "analysis_prompt": "Analyze these firewall logs for security issues, unusual patterns, and failed authentication attempts. Provide findings in JSON format."
}
```

2. **Mount SSH keys**

Update `docker-compose.yml` to mount your SSH keys:

```yaml
volumes:
  - ~/.ssh:/root/.ssh:ro
```

3. **Restart the container**

```bash
docker-compose restart netmon
```

## Configuration

### Environment Variables

See `.env.example` for all available options:

| Variable | Required | Description | Runtime Configurable |
|----------|----------|-------------|---------------------|
| `DISCORD_WEBHOOK_URL` | Yes* | Discord webhook for alerts | Yes (via UI/API) |
| `LLM_API_URL` | Yes | LLM API endpoint | No |
| `LLM_API_KEY` | Yes | LLM API key | No |
| `LLM_DEFAULT_MODEL` | No | Default model (default: claude-sonnet-4.5) | No |
| `HEALTHCHECKS_URL` | No* | Upstream monitoring URL | Yes (via UI/API) |
| `BUSINESS_HOURS_START` | No | Start time (default: 08:00) | No |
| `BUSINESS_HOURS_END` | No | End time (default: 18:00) | No |
| `BUSINESS_HOURS_DAYS` | No | Active days (default: 1,2,3,4,5) | No |
| `BUSINESS_HOURS_TIMEZONE` | No | Timezone (default: America/New_York) | No |

\* Can be configured via environment or runtime (database takes precedence)

### Schedule Types

- **`always`**: Monitor 24/7
  - Alerts immediately if heartbeat is late
  - No time-based restrictions

- **`business_hours`**: Monitor only during configured business hours
  - **Schedule-aware**: Prevents false alerts at window start
  - Example: If window is 8am-10am, won't alert at 8:01am if last heartbeat was yesterday
  - Only checks frequency within the monitoring window

- **`custom`**: Custom cron-like schedules (not yet implemented)

### Schedule-Aware Monitoring Logic

The system intelligently handles monitoring windows to prevent false alerts:

**Example Scenario**:
- Schedule: 8am-10am CST daily
- Frequency: 5 minutes
- Grace: 60 seconds
- Last heartbeat: Yesterday 9:55am

**Behavior**:
- ❌ **Old logic**: Would alert at 8:01am (22 hours > 6 minutes)
- ✅ **New logic**: Waits until 8:07am before alerting
  - Calculation: `window_start (8:00) + frequency (5min) + grace (60s) = 8:06`
  - Alerts only if no heartbeat by 8:07am

This prevents false alerts when hosts legitimately stop during off-hours.

## API Reference

### Heartbeat Endpoints

- **`POST|GET /api/v1/heartbeat/{host_id}`** - Receive heartbeat
  - Supports both GET and POST methods
  - Token via query parameter: `?token=<token>` (recommended)
  - OR via header: `Authorization: Bearer <token>`
  - Returns: `{"status": "success", "message": "Heartbeat received", ...}`

- **`GET /api/v1/heartbeat/{host_id}/history`** - Get heartbeat history
  - Query params: `limit` (default: 100)
  - Returns: List of recent heartbeats with timestamps

### Host Management

- **`GET /api/v1/hosts`** - List all hosts
  - Returns: Array of hosts with status

- **`GET /api/v1/hosts/{host_id}`** - Get host details
  - Returns: Host details including **full heartbeat URL with token**

- **`POST /api/v1/hosts`** - Register new host
  - Body: `{name, host_id, token, cron_expression, schedule_type, ...}`
  - Returns: Host details with **heartbeat URL including token**

- **`PUT /api/v1/hosts/{host_id}`** - Update host
  - Body: Updated host fields
  - Returns: Updated host details

- **`DELETE /api/v1/hosts/{host_id}`** - Delete host
  - Returns: Success confirmation

- **`POST /api/v1/hosts/generate-token`** - Generate secure token
  - Returns: `{"token": "..."}`

- **`GET /api/v1/hosts/config/all`** - Get all host configurations
  - Returns: All hosts with full configuration details

- **`PATCH /api/v1/hosts/{host_id}/config`** - Quick update of frequency/schedule
  - Query params: `frequency_seconds`, `grace_period_seconds`, `schedule_type`
  - Returns: Updated host

### Settings & Configuration

- **`GET /api/v1/settings/webhook`** - Get webhook configuration
  - Returns: Current webhook URL and source (database/environment)

- **`PUT /api/v1/settings/webhook`** - Update webhook URL
  - Body: `{"webhook_url": "..."}`
  - Returns: Updated configuration

- **`GET /api/v1/settings/upstream`** - Get upstream monitoring config
  - Returns: Upstream monitoring settings (enabled, url, frequency)

- **`PUT /api/v1/settings/upstream`** - Update upstream monitoring
  - Body: `{"enabled": true, "url": "...", "frequency_seconds": 300}`
  - Returns: Updated configuration

- **`GET /api/v1/settings/all`** - Get all system settings
  - Returns: All configuration settings

### Dashboard & Configuration

- **`GET /api/v1/dashboard`** - HTML status dashboard
  - Returns: Full-featured dashboard with:
    - Host status summary
    - Summary table with **copy buttons for URLs**
    - Recent alerts
    - Auto-refresh every 30 seconds

- **`GET /api/v1/dashboard/data`** - Dashboard data (JSON)
  - Returns: `{hosts[], recent_alerts[], stats}`
  - Host objects include **complete heartbeat URLs with tokens**

- **`GET /api/v1/config`** - HTML configuration manager
  - Returns: Configuration UI with:
    - Host management table with **copy buttons**
    - Add/Edit/Delete host forms
    - Webhook configuration
    - Upstream monitoring configuration

### Health

- **`GET /api/v1/health`** - System health check
  - Returns: `{status, timestamp, version, database}`

## Architecture

The system runs in a **single Docker container** for easy management. All services run concurrently:

### Container: `netmon`

**FastAPI API Server** (Port 8080)
- Receives heartbeats (GET or POST)
- Serves dashboards and configuration UI
- Provides REST API
- Handles runtime configuration updates

**Background Scheduler** (APScheduler)
- Checks for missing heartbeats (every 1 min)
- Runs log analysis (every 30 min)
- Database cleanup (daily at 3 AM UTC)
- Health checks (hourly)
- **Upstream heartbeat** (every 5 min)

**Internet Monitor**
- Connectivity checks (every 5 min)
- Healthchecks.io pinging
- Alerts on outages

### Data Flow

```
Client Host → Heartbeat (GET/POST) → API → Database
                                            ↓
Scheduler → Check Database (Schedule-Aware) → Missing? → Alert → Discord
                                                               ↓
SSH → Logs → LLM → Analysis → Database → Alert → Discord
                                                    ↓
Internet Check → Success → Healthchecks.io
              → Failure → Alert → Discord
                                    ↓
Upstream Monitor → Send Heartbeat → External Service (healthchecks.io)
```

### Database Schema

**Tables**:
- `hosts` - Host configurations and status
- `heartbeats` - Heartbeat timestamps and source IPs
- `alerts` - Alert history
- `log_analyses` - LLM analysis results
- `config` - Runtime configuration (webhook, upstream monitoring)

**Database Priority**:
- Webhook URL: Database > Environment
- Upstream monitoring: Database > Environment

This allows runtime configuration without container restarts.

## Monitoring the Monitor

To ensure the monitoring system itself is healthy, use **Upstream Monitoring**:

### Setup with Healthchecks.io

1. **Create a check** at [https://healthchecks.io](https://healthchecks.io)
2. **Copy the ping URL** (e.g., `https://hc-ping.com/12345678-abcd-...`)
3. **Configure via UI**:
   - Visit [http://localhost:8080/api/v1/config](http://localhost:8080/api/v1/config)
   - Enable "Upstream Monitoring"
   - Paste the URL
   - Save

4. **Verify**: Check healthchecks.io dashboard
   - Monitor should show "Up" status
   - If the hub goes down, you'll receive an alert

### Setup with Uptime Kuma

1. **Create a monitor** in Uptime Kuma
2. **Set type** to "HTTP(s) - Keyword" or "Push"
3. **Copy the push URL** or create a heartbeat-style URL
4. **Configure** in the monitoring hub (same as above)

## Deployment

### Production Checklist

- [ ] Use HTTPS (reverse proxy with SSL/TLS)
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Enable upstream monitoring
- [ ] Configure proper business hours if needed
- [ ] Test schedule-aware monitoring logic
- [ ] Set up log rotation for container logs
- [ ] Monitor disk usage
- [ ] Configure alert thresholds appropriately

### Docker Compose

The system uses a single container for simplicity:

```yaml
services:
  netmon:
    build: .
    container_name: netmon
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Backup

**Database backup**:
```bash
docker exec netmon sqlite3 /app/data/db.sqlite ".backup '/app/data/db_backup.sqlite'"
```

**Full backup**:
```bash
tar -czf netmon-backup-$(date +%Y%m%d).tar.gz data/ logs/ .env
```

## Troubleshooting

### Heartbeat Not Received

1. **Check the URL**: Verify you're using the complete URL with token
   - Copy from dashboard using 📋 button
   - URL should be: `http://server:8080/api/v1/heartbeat/host-id?token=TOKEN`

2. **Test manually**:
   ```bash
   curl "http://server:8080/api/v1/heartbeat/host-id?token=TOKEN"
   ```

3. **Check container logs**:
   ```bash
   docker logs netmon --tail 100
   ```

4. **Verify token**: Tokens are case-sensitive

### False Alerts During Window Start

This is **fixed** with schedule-aware monitoring:

- Business hours hosts now use window-start + frequency logic
- No more alerts at 8:01am if last heartbeat was yesterday
- Configure grace period appropriately for your needs

### Copy Buttons Not Working

Copy buttons use modern Clipboard API:

- **Requires HTTPS** in production (or localhost for testing)
- Check browser console for errors
- Ensure JavaScript is enabled
- Try refreshing the page

### Upstream Monitoring Not Working

1. **Check configuration**:
   ```bash
   curl http://localhost:8080/api/v1/settings/upstream
   ```

2. **Verify enabled**: `"enabled": true`

3. **Check logs**:
   ```bash
   docker logs netmon | grep -i "upstream"
   ```

4. **Test URL manually**:
   ```bash
   curl "https://hc-ping.com/your-uuid"
   ```

### Container Won't Start

1. **Check logs**:
   ```bash
   docker logs netmon
   ```

2. **Verify environment**:
   ```bash
   docker exec netmon env | grep -E "DISCORD|LLM"
   ```

3. **Check database**:
   ```bash
   ls -la data/
   ```

4. **Rebuild**:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

## Development

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run API server
python -m uvicorn src.api.main:app --reload --port 8080

# Run scheduler (separate terminal)
python -m src.services.scheduler_service

# Run internet monitor (separate terminal)
python -m src.services.internet_monitor
```

### Testing

```bash
# Test heartbeat
curl -X POST "http://localhost:8080/api/v1/heartbeat/test-host?token=test-token"

# Test with Bearer header
curl -X POST http://localhost:8080/api/v1/heartbeat/test-host \
  -H "Authorization: Bearer test-token"

# Get dashboard data
curl http://localhost:8080/api/v1/dashboard/data

# Test upstream monitoring
curl http://localhost:8080/api/v1/settings/upstream
```

### Project Structure

```
network-monitoring/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI app
│   │   └── routes/
│   │       ├── heartbeat.py     # Heartbeat endpoints (GET/POST)
│   │       ├── hosts.py         # Host management
│   │       ├── dashboard.py     # Dashboard UI
│   │       ├── config_view.py   # Config UI
│   │       └── settings.py      # Runtime settings API
│   ├── database/
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   └── db.py                # Database connection
│   ├── services/
│   │   ├── scheduler_service.py # Background scheduler
│   │   ├── alert_service.py     # Alert handling
│   │   ├── log_analyzer.py      # LLM log analysis
│   │   ├── internet_monitor.py  # Connectivity checks
│   │   └── upstream_monitor.py  # Self-monitoring
│   ├── utils/
│   │   ├── discord.py           # Discord webhook client
│   │   ├── llm_client.py        # LLM API client
│   │   ├── ssh_client.py        # SSH wrapper
│   │   └── schedule_utils.py    # Schedule-aware logic
│   └── config.py                # Configuration
├── scripts/
│   ├── setup.sh                 # Initial setup
│   ├── add-host.py              # Add host script
│   ├── client-heartbeat.sh      # Client heartbeat script
│   └── start-services.sh        # Container startup
├── data/                        # Database and persistent data
├── logs/                        # Application logs
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md
│   ├── REQUIREMENTS.md
│   ├── PROJECT_STATUS.md
│   └── BUGLOG.md
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Version History

### v1.2.0 (2025-01-15) - Schedule-Aware & Upstream Monitoring
- ✅ Schedule-aware monitoring logic (prevents false alerts)
- ✅ Runtime webhook URL configuration
- ✅ Upstream monitoring (self-monitoring)
- ✅ Token-embedded heartbeat URLs
- ✅ Copy buttons in Dashboard and Config UI
- ✅ GET method support for heartbeat endpoint
- ✅ Database-backed configuration

### v1.1.0 (2025-01-06) - Container Consolidation
- ✅ Single Docker container deployment
- ✅ Configuration management UI
- ✅ Quick config update endpoints

### v1.0.0 (2025-11-15) - Initial Release
- ✅ Heartbeat monitoring
- ✅ LLM-powered log analysis
- ✅ Internet connectivity monitoring
- ✅ Discord alerts
- ✅ Web dashboard
- ✅ Business hours support

## License

MIT License - See LICENSE file for details

## Support

- **Documentation**: See `docs/` directory
- **Issues**: Check `docs/BUGLOG.md`
- **Architecture**: See `docs/ARCHITECTURE.md`
- **Status**: See `docs/PROJECT_STATUS.md`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Credits

Built with:
- FastAPI
- SQLAlchemy
- APScheduler
- Discord Webhooks
- LLM APIs (Claude, GPT, GLM)

---

**Production Ready**: 92%

Ready for deployment with proper SSL/TLS configuration and security hardening.
