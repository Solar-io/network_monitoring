# Network Monitoring System

A comprehensive Python-based network and system monitoring platform with heartbeat monitoring, LLM-powered log analysis, and internet connectivity tracking.

## Features

- 🔄 **Heartbeat Monitoring**: Track host availability via unique URLs
- 🤖 **LLM Log Analysis**: Analyze firewall/system logs using AI (Claude, GPT, GLM)
- 🌐 **Internet Monitoring**: Track connectivity with healthchecks.io integration
- 📢 **Discord Alerts**: Rich webhook-based notifications
- ⏰ **Business Hours Support**: Schedule monitoring windows
- 🐳 **Single Container Deployment**: Everything runs in one Docker container
- 📊 **Web Dashboard**: Real-time monitoring dashboard
- ⚙️ **Easy Configuration**: View and edit host settings via web UI or API

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Discord webhook URL
- LLM API access (unified endpoint supporting Claude/GPT/GLM)
- (Optional) Healthchecks.io account

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

# Optional
HEALTHCHECKS_URL=https://hc-ping.com/your-uuid
```

4. **Start the system**

```bash
docker-compose up -d
```

5. **Access the dashboards**

- **Status Dashboard**: [http://localhost:8080/api/v1/dashboard](http://localhost:8080/api/v1/dashboard)
- **Configuration Manager**: [http://localhost:8080/api/v1/config](http://localhost:8080/api/v1/config)

## Usage

### Registering a Host

Use the `add-host.py` script to register a new host:

```bash
python scripts/add-host.py \
  --name "Web Server 01" \
  --host-id web01 \
  --frequency 300 \
  --schedule always
```

The script will:
- Generate a secure token
- Register the host with the API
- Display setup instructions for the client

### Client Setup

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

### Managing Host Configurations

You can view and update host configurations in multiple ways:

**1. Web Configuration Manager** (Easiest)

Visit [http://localhost:8080/api/v1/config](http://localhost:8080/api/v1/config) to:
- View all host configurations in a table
- Edit heartbeat frequency, grace period, and schedule
- See current status and settings at a glance

**2. API Endpoints**

View all configurations:
```bash
curl http://localhost:8080/api/v1/hosts/config/all
```

Update a host's configuration:
```bash
curl -X PATCH "http://localhost:8080/api/v1/hosts/web01/config?frequency_seconds=600&schedule_type=business_hours"
```

**3. Programmatically**

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

### Configuring Log Analysis

To enable log analysis for a host (e.g., firewall):

1. **Edit the host configuration**

Add `log_analysis_config` to your host (via API or `config/hosts.yaml`):

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

3. **Restart the scheduler**

```bash
docker-compose restart scheduler
```

## Configuration

### Environment Variables

See `.env.example` for all available options:

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_WEBHOOK_URL` | Yes | Discord webhook for alerts |
| `LLM_API_URL` | Yes | LLM API endpoint |
| `LLM_API_KEY` | Yes | LLM API key |
| `LLM_DEFAULT_MODEL` | No | Default model (default: claude-sonnet-4.5) |
| `HEALTHCHECKS_URL` | No | Healthchecks.io ping URL |
| `BUSINESS_HOURS_START` | No | Start time (default: 08:00) |
| `BUSINESS_HOURS_END` | No | End time (default: 18:00) |
| `BUSINESS_HOURS_DAYS` | No | Active days (default: 1,2,3,4,5) |
| `BUSINESS_HOURS_TIMEZONE` | No | Timezone (default: America/New_York) |

### Host Configuration

Hosts can be configured via:

1. **API** (recommended for dynamic changes):
   - `POST /api/v1/hosts` - Register new host
   - `PUT /api/v1/hosts/{host_id}` - Update host
   - `DELETE /api/v1/hosts/{host_id}` - Remove host

2. **YAML file** (`config/hosts.yaml`):
   - See `config/hosts.yaml.example` for examples
   - Requires database import/sync (not yet implemented)

3. **Script** (`scripts/add-host.py`):
   - Interactive host registration
   - Generates secure tokens
   - Provides client setup instructions

### Schedule Types

- `always`: Monitor 24/7
- `business_hours`: Monitor only during configured business hours
- `custom`: Custom cron-like schedules (not yet implemented)

## API Reference

### Heartbeat Endpoints

- `POST /api/v1/heartbeat/{host_id}` - Receive heartbeat
  - Header: `Authorization: Bearer <token>`

- `GET /api/v1/heartbeat/{host_id}/history` - Get heartbeat history

### Host Management

- `GET /api/v1/hosts` - List all hosts
- `GET /api/v1/hosts/{host_id}` - Get host details
- `POST /api/v1/hosts` - Register new host
- `PUT /api/v1/hosts/{host_id}` - Update host
- `DELETE /api/v1/hosts/{host_id}` - Delete host
- `POST /api/v1/hosts/generate-token` - Generate secure token
- `GET /api/v1/hosts/config/all` - Get all host configurations
- `PATCH /api/v1/hosts/{host_id}/config` - Quick update of frequency/schedule

### Dashboard & Configuration

- `GET /api/v1/dashboard` - HTML status dashboard
- `GET /api/v1/dashboard/data` - Dashboard data (JSON)
- `GET /api/v1/config` - HTML configuration manager

### Health

- `GET /api/v1/health` - System health check

## Architecture

The system runs in a **single Docker container** for easy management. All services run concurrently:

**Container: `netmon`**
- **FastAPI API Server** (Port 8080)
  - Receives heartbeats
  - Serves dashboards and configuration UI
  - Provides REST API

- **Background Scheduler** (APScheduler)
  - Checks for missing heartbeats (every 1 min)
  - Runs log analysis (every 30 min)
  - Database cleanup (daily at 3 AM UTC)
  - Health checks (hourly)

- **Internet Monitor**
  - Connectivity checks (every 5 min)
  - Healthchecks.io pinging
  - Alerts on outages

### Data Flow

```
Client Host → Heartbeat → API → Database
                                    ↓
Scheduler → Check Database → Missing? → Alert → Discord
                                                    ↓
SSH → Logs → LLM → Analysis → Database → Alert → Discord
                                                    ↓
Internet Check → Success → Healthchecks.io
              → Failure → Alert → Discord
```

## Monitoring the Monitor

The system monitors itself:

- **Health Check Endpoint**: `/api/v1/health`
- **Hourly Health Checks**: Verifies database and configuration
- **Internet Monitor**: Validates outbound connectivity
- **Healthchecks.io**: Meta-monitoring (monitors the monitor)

## Troubleshooting

### Heartbeats Not Being Received

1. Check client can reach the server:
   ```bash
   curl http://your-server:8080/api/v1/health
   ```

2. Verify token is correct:
   ```bash
   curl -X POST http://your-server:8080/api/v1/heartbeat/web01 \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. Check container logs:
   ```bash
   docker-compose logs netmon
   ```

### Log Analysis Not Working

1. Verify SSH connectivity from container:
   ```bash
   docker-compose exec netmon ssh admin@192.168.1.1
   ```

2. Check SSH keys are mounted:
   ```bash
   docker-compose exec netmon ls -la /root/.ssh
   ```

3. Review container logs:
   ```bash
   docker-compose logs netmon
   ```

### Discord Alerts Not Sending

1. Verify webhook URL in `.env`:
   ```bash
   docker-compose exec netmon env | grep DISCORD
   ```

2. Test webhook manually:
   ```bash
   curl -X POST "YOUR_WEBHOOK_URL" \
     -H "Content-Type: application/json" \
     -d '{"content": "Test message"}'
   ```

3. Check alert service logs:
   ```bash
   docker-compose logs | grep discord
   ```

## Maintenance

### View Logs

```bash
# View container logs
docker-compose logs -f netmon

# With tail
docker-compose logs -f --tail=100 netmon
```

### Restart Services

```bash
# Restart the container (restarts all services)
docker-compose restart netmon
```

### Update System

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Backup Database

```bash
# Backup
cp data/db.sqlite data/db.sqlite.backup-$(date +%Y%m%d)

# Restore
cp data/db.sqlite.backup-YYYYMMDD data/db.sqlite
docker-compose restart
```

## Development

### Running Locally (without Docker)

1. **Install dependencies**

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Set environment variables**

```bash
export DISCORD_WEBHOOK_URL="..."
export LLM_API_URL="..."
export LLM_API_KEY="..."
export DATABASE_URL="sqlite:///data/db.sqlite"
```

3. **Initialize database**

```bash
python -c "from src.database import init_db; init_db()"
```

4. **Run API server**

```bash
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080
```

5. **Run scheduler** (in separate terminal)

```bash
python -m src.services.scheduler_service
```

6. **Run internet monitor** (in separate terminal)

```bash
python -m src.services.internet_monitor
```

### Running Tests

```bash
pytest tests/ -v
```

## Security Considerations

- **Tokens**: Use strong, randomly generated tokens for each host
- **SSH Keys**: Mount as read-only, don't embed in images
- **Secrets**: Keep `.env` out of version control (use `.gitignore`)
- **API Access**: In production, restrict API access via firewall
- **HTTPS**: Use reverse proxy (nginx, Caddy) for HTTPS in production

## Future Enhancements

- PostgreSQL support for better concurrency
- Web UI for host management
- Alert acknowledgment workflow
- Historical metrics and dashboards
- Grafana/Prometheus integration
- Multi-region deployment support
- Custom schedule expressions (cron-like)
- Auto-remediation capabilities

## License

[Your License Here]

## Support

For issues and questions:
- Check the troubleshooting section
- Review logs: `docker-compose logs`
- Open an issue on GitHub

---

Built with ❤️ using Python, FastAPI, and Docker
