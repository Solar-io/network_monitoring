# Network Monitoring System - Usage Examples

Last updated: 2025-01-15
Version: 1.2.0

## Quick Start Examples

### Example 1: Monitor a Web Server (Simplest Method)

**Scenario**: You have a web server that should send heartbeats every 5 minutes.

**Steps**:

1. **Add the host via Dashboard UI**:
   - Navigate to `http://your-monitor:8080/api/v1/config`
   - Click "Add New Host"
   - Fill in:
     - Name: `web-server-01`
     - Frequency: `300` seconds (5 minutes)
     - Grace Period: `60` seconds
     - Schedule: `always`
   - Click "Add Host"

2. **Copy the heartbeat URL**:
   - Find `web-server-01` in the host list
   - Click the 📋 Copy button next to the heartbeat URL
   - The complete URL is now in your clipboard:
     ```
     http://your-monitor:8080/api/v1/heartbeat/web01?token=abc123xyz
     ```

3. **Set up cron job on the web server**:
   ```bash
   # Edit crontab
   crontab -e

   # Add this line (paste the URL you copied):
   */5 * * * * curl -s "http://your-monitor:8080/api/v1/heartbeat/web01?token=abc123xyz" > /dev/null 2>&1
   ```

4. **Verify it's working**:
   - Go to `http://your-monitor:8080/api/v1/dashboard`
   - After 5 minutes, you should see `web-server-01` status as "up"

**That's it!** If the cron job fails to run, you'll get a Discord alert after 5 minutes + 60 seconds = 6 minutes.

---

### Example 2: Monitor a Backup Server (Business Hours Only)

**Scenario**: Backup server runs backups only during business hours (8am-6pm weekdays). You don't want alerts outside business hours.

**Steps**:

1. **Add host with business_hours schedule**:
   ```bash
   # Via API (or use the Config UI)
   curl -X POST http://your-monitor:8080/api/v1/hosts \
     -H "Content-Type: application/json" \
     -d '{
       "name": "backup-server",
       "expected_frequency_seconds": 3600,
       "grace_period_seconds": 300,
       "schedule_type": "business_hours"
     }'
   ```

2. **Copy the returned heartbeat URL** from the response:
   ```json
   {
     "name": "backup-server",
     "host_id": "backup-server",
     "heartbeat_url": "http://your-monitor:8080/api/v1/heartbeat/backup-server?token=xyz789abc",
     "status": "unknown"
   }
   ```

3. **Add to backup script**:
   ```bash
   #!/bin/bash
   # backup.sh

   # Your backup commands here
   rsync -avz /data /backup

   # Signal success to monitoring system
   curl "http://your-monitor:8080/api/v1/heartbeat/backup-server?token=xyz789abc"
   ```

4. **Schedule the backup** (runs 9am weekdays):
   ```bash
   # crontab
   0 9 * * 1-5 /opt/scripts/backup.sh
   ```

**Behavior**:
- ✅ Monday 9:00am: Backup runs, heartbeat sent
- ✅ Monday 10:00am: If no heartbeat received by 10:01am + 5min grace = 10:06am, alert sent
- ✅ Friday 6:00pm: Monitoring suspends
- ✅ Monday 8:00am: Monitoring resumes
- ❌ Monday 8:01am: **NO FALSE ALERT** (schedule-aware logic waits until 9:00am + 1hr + 5min = 10:05am)

---

### Example 3: Monitor Docker Container Health

**Scenario**: Monitor a Docker container's health by having it send heartbeats.

**Docker Compose with Heartbeat**:

```yaml
version: '3.8'

services:
  myapp:
    image: myapp:latest
    environment:
      # Pass the complete heartbeat URL
      HEARTBEAT_URL: "http://monitor:8080/api/v1/heartbeat/myapp?token=container123"
    healthcheck:
      test: ["CMD", "curl", "-f", "$HEARTBEAT_URL"]
      interval: 5m
      timeout: 10s
      retries: 3
```

**Alternative: Sidecar Pattern**:

```yaml
version: '3.8'

services:
  myapp:
    image: myapp:latest
    # Your app doesn't need to know about monitoring

  heartbeat:
    image: curlimages/curl:latest
    command: sh -c 'while true; do curl -s "http://monitor:8080/api/v1/heartbeat/myapp?token=container123"; sleep 300; done'
    restart: unless-stopped
```

---

### Example 4: Monitor Kubernetes Pod

**Scenario**: Monitor a Kubernetes deployment to ensure pods are running.

**Using CronJob**:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: heartbeat-myapp
spec:
  schedule: "*/5 * * * *"  # Every 5 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: heartbeat
            image: curlimages/curl:latest
            command:
            - /bin/sh
            - -c
            - curl -s "http://monitor.monitoring.svc.cluster.local:8080/api/v1/heartbeat/myapp?token=k8s123"
          restartPolicy: OnFailure
```

**Using Sidecar Container**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    spec:
      containers:
      - name: myapp
        image: myapp:latest
        # Your application container

      - name: heartbeat
        image: curlimages/curl:latest
        command:
        - /bin/sh
        - -c
        - while true; do curl -s "http://monitor.monitoring.svc.cluster.local:8080/api/v1/heartbeat/myapp?token=k8s123"; sleep 300; done
```

---

### Example 5: Monitor a Systemd Service

**Scenario**: Monitor that a systemd service is running and healthy.

**Create heartbeat timer**:

```bash
# /etc/systemd/system/myservice-heartbeat.service
[Unit]
Description=Send heartbeat for myservice
Requires=myservice.service

[Service]
Type=oneshot
ExecStart=/usr/bin/curl -s "http://monitor:8080/api/v1/heartbeat/myservice?token=systemd456"
User=nobody
```

```bash
# /etc/systemd/system/myservice-heartbeat.timer
[Unit]
Description=Heartbeat timer for myservice
Requires=myservice-heartbeat.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
Unit=myservice-heartbeat.service

[Install]
WantedBy=timers.target
```

**Enable and start**:

```bash
sudo systemctl enable myservice-heartbeat.timer
sudo systemctl start myservice-heartbeat.timer
```

**Verify**:

```bash
sudo systemctl status myservice-heartbeat.timer
sudo systemctl list-timers
```

---

### Example 6: Monitor a Python Application

**Scenario**: Python app sends heartbeat after completing critical tasks.

```python
#!/usr/bin/env python3
import requests
import logging
from datetime import datetime

# Configuration
HEARTBEAT_URL = "http://monitor:8080/api/v1/heartbeat/python-app?token=python789"

def send_heartbeat():
    """Send heartbeat to monitoring system"""
    try:
        response = requests.get(HEARTBEAT_URL, timeout=10)
        if response.status_code == 200:
            logging.info(f"Heartbeat sent successfully at {datetime.now()}")
            return True
        else:
            logging.error(f"Heartbeat failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logging.error(f"Failed to send heartbeat: {e}")
        return False

def main():
    logging.basicConfig(level=logging.INFO)

    # Your application logic
    process_data()

    # Send heartbeat after successful completion
    send_heartbeat()

if __name__ == "__main__":
    main()
```

**Scheduled version** (runs every hour):

```python
#!/usr/bin/env python3
import requests
import schedule
import time
import logging

HEARTBEAT_URL = "http://monitor:8080/api/v1/heartbeat/python-app?token=python789"

def send_heartbeat():
    try:
        requests.get(HEARTBEAT_URL, timeout=10)
        logging.info("Heartbeat sent")
    except Exception as e:
        logging.error(f"Heartbeat failed: {e}")

def do_work():
    # Your actual work
    logging.info("Processing data...")
    process_data()
    send_heartbeat()

# Schedule heartbeat every hour
schedule.every().hour.do(do_work)

logging.basicConfig(level=logging.INFO)
logging.info("Starting scheduled tasks...")

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

### Example 7: Monitor Multiple Services on One Host

**Scenario**: Single server runs multiple services, each monitored independently.

**Setup**:

1. **Register each service separately**:
   - `nginx-service` - expects heartbeat every 5 minutes
   - `postgres-service` - expects heartbeat every 10 minutes
   - `redis-service` - expects heartbeat every 5 minutes

2. **Create wrapper script** (`/opt/monitoring/heartbeat.sh`):

```bash
#!/bin/bash
# /opt/monitoring/heartbeat.sh

BASE_URL="http://monitor:8080/api/v1/heartbeat"

# Function to send heartbeat
send_heartbeat() {
    local service=$1
    local token=$2
    local url="${BASE_URL}/${service}?token=${token}"

    if curl -sf "$url" > /dev/null 2>&1; then
        logger "Heartbeat sent for $service"
        return 0
    else
        logger "Failed to send heartbeat for $service"
        return 1
    fi
}

# Check if service is running and send heartbeat
check_and_send() {
    local service_name=$1
    local systemd_service=$2
    local token=$3

    if systemctl is-active --quiet "$systemd_service"; then
        send_heartbeat "$service_name" "$token"
    else
        logger "$systemd_service is not running, skipping heartbeat"
    fi
}

# Main execution
case "$1" in
    nginx)
        check_and_send "nginx-service" "nginx" "nginx_token_123"
        ;;
    postgres)
        check_and_send "postgres-service" "postgresql" "postgres_token_456"
        ;;
    redis)
        check_and_send "redis-service" "redis" "redis_token_789"
        ;;
    all)
        check_and_send "nginx-service" "nginx" "nginx_token_123"
        check_and_send "postgres-service" "postgresql" "postgres_token_456"
        check_and_send "redis-service" "redis" "redis_token_789"
        ;;
    *)
        echo "Usage: $0 {nginx|postgres|redis|all}"
        exit 1
        ;;
esac
```

3. **Setup cron jobs**:

```bash
# crontab -e
*/5 * * * * /opt/monitoring/heartbeat.sh nginx
*/10 * * * * /opt/monitoring/heartbeat.sh postgres
*/5 * * * * /opt/monitoring/heartbeat.sh redis
```

---

### Example 8: Monitor Network Connectivity from Remote Sites

**Scenario**: Monitor that remote office networks are reachable.

**Remote site script** (`/opt/monitoring/connectivity-check.sh`):

```bash
#!/bin/bash
# Remote site connectivity checker

SITE_NAME="office-chicago"
HEARTBEAT_URL="http://monitor.hq.example.com:8080/api/v1/heartbeat/${SITE_NAME}?token=chicago123"

# Test internet connectivity
if ping -c 3 8.8.8.8 > /dev/null 2>&1; then
    # Internet is up, send heartbeat
    curl -s "$HEARTBEAT_URL"
    logger "Connectivity check passed for $SITE_NAME"
else
    logger "Internet down at $SITE_NAME - heartbeat not sent"
fi
```

**Cron setup at each remote site**:

```bash
*/10 * * * * /opt/monitoring/connectivity-check.sh
```

**Result**: Central monitoring knows when remote sites lose connectivity (no heartbeat received).

---

### Example 9: Using GET Method for Browser Testing

**Scenario**: Quickly test heartbeat endpoint before setting up automation.

**Just paste URL in browser**:

```
http://your-monitor:8080/api/v1/heartbeat/test-host?token=your_token_here
```

**Browser shows**:

```json
{
  "message": "Heartbeat received",
  "host_id": "test-host",
  "timestamp": "2025-01-15T14:30:00Z"
}
```

**Check dashboard**:
- Navigate to `http://your-monitor:8080/api/v1/dashboard`
- See `test-host` status updated to "up"
- Last Seen timestamp matches current time

**This is perfect for**:
- Testing before deploying scripts
- Troubleshooting authentication issues
- Verifying network connectivity
- Quick manual check-ins

---

### Example 10: Automated Testing of the Monitoring System

**Scenario**: Test your monitoring system is working correctly.

**Test script** (`test_monitoring.sh`):

```bash
#!/bin/bash
set -e

MONITOR_URL="http://localhost:8080"
TEST_HOST="test-automated"

echo "=== Monitoring System Test ==="

# 1. Create test host
echo "Creating test host..."
RESPONSE=$(curl -s -X POST "${MONITOR_URL}/api/v1/hosts" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-automated",
    "expected_frequency_seconds": 60,
    "grace_period_seconds": 30,
    "schedule_type": "always"
  }')

HEARTBEAT_URL=$(echo "$RESPONSE" | jq -r '.heartbeat_url')
echo "Heartbeat URL: $HEARTBEAT_URL"

# 2. Send heartbeat
echo "Sending heartbeat..."
curl -s "$HEARTBEAT_URL"

# 3. Check status via API
echo "Checking host status..."
sleep 2
STATUS=$(curl -s "${MONITOR_URL}/api/v1/hosts/${TEST_HOST}" | jq -r '.status')

if [ "$STATUS" = "up" ]; then
    echo "✓ Test PASSED: Host status is 'up'"
else
    echo "✗ Test FAILED: Host status is '$STATUS' (expected 'up')"
    exit 1
fi

# 4. Wait for missed heartbeat (should trigger alert after 90 seconds)
echo "Waiting 2 minutes to test alert system..."
sleep 120

# 5. Check status again (should be 'down')
STATUS=$(curl -s "${MONITOR_URL}/api/v1/hosts/${TEST_HOST}" | jq -r '.status')

if [ "$STATUS" = "down" ]; then
    echo "✓ Test PASSED: Host correctly marked as 'down'"
else
    echo "✗ Test FAILED: Host status is '$STATUS' (expected 'down')"
    exit 1
fi

# 6. Send heartbeat to recover
echo "Sending recovery heartbeat..."
curl -s "$HEARTBEAT_URL"
sleep 2

STATUS=$(curl -s "${MONITOR_URL}/api/v1/hosts/${TEST_HOST}" | jq -r '.status')

if [ "$STATUS" = "up" ]; then
    echo "✓ Test PASSED: Host recovered to 'up'"
else
    echo "✗ Test FAILED: Host status is '$STATUS' (expected 'up')"
    exit 1
fi

# 7. Cleanup
echo "Cleaning up..."
curl -s -X DELETE "${MONITOR_URL}/api/v1/hosts/${TEST_HOST}"

echo "=== All Tests PASSED ==="
```

---

## Configuration Examples

### Example 11: Configure Upstream Monitoring (Self-Monitoring)

**Scenario**: Monitor the monitoring hub itself using healthchecks.io.

**Via UI**:

1. Navigate to `http://your-monitor:8080/api/v1/config`
2. Scroll to "Upstream Monitoring" section
3. Fill in:
   - **Enable**: ✓ (checked)
   - **URL**: `https://hc-ping.com/your-uuid-here`
   - **Frequency**: `300` (5 minutes)
4. Click "Save Upstream Settings"

**Via API**:

```bash
curl -X PUT http://your-monitor:8080/api/v1/settings/upstream \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "url": "https://hc-ping.com/your-uuid-here",
    "frequency_seconds": 300
  }'
```

**Result**:
- Monitoring hub pings healthchecks.io every 5 minutes
- If hub goes down, healthchecks.io doesn't receive ping
- Healthchecks.io sends alert to your configured notification channel
- **Meta-monitoring complete!**

---

### Example 12: Update Discord Webhook at Runtime

**Scenario**: Change Discord webhook URL without restarting container.

**Via UI**:

1. Navigate to `http://your-monitor:8080/api/v1/config`
2. Find "Discord Webhook URL" field
3. Update to new webhook URL
4. Click "Save Webhook"

**Via API**:

```bash
curl -X PUT http://your-monitor:8080/api/v1/settings/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://discord.com/api/webhooks/NEW_WEBHOOK_ID/NEW_TOKEN"
  }'
```

**Verify**:

```bash
# Get current settings
curl http://your-monitor:8080/api/v1/settings/all | jq
```

**Result**: Next alert uses new webhook URL immediately, no restart required.

---

## Troubleshooting Examples

### Example 13: Debug "Method Not Allowed" Error

**Problem**:
```json
{"detail":"Method Not Allowed"}
```

**Solution**: You're likely using an old URL format or wrong method.

**Check your URL**:
```bash
# ✗ WRONG (missing token query parameter with POST)
curl -X POST http://monitor:8080/api/v1/heartbeat/myhost \
  -H "Authorization: Bearer mytoken"

# ✓ CORRECT (v1.2.0 - token in URL, works with GET)
curl "http://monitor:8080/api/v1/heartbeat/myhost?token=mytoken"

# ✓ ALSO CORRECT (POST with token in URL)
curl -X POST "http://monitor:8080/api/v1/heartbeat/myhost?token=mytoken"

# ✓ ALSO CORRECT (Bearer header still works)
curl -X POST http://monitor:8080/api/v1/heartbeat/myhost \
  -H "Authorization: Bearer mytoken"
```

---

### Example 14: Debug Copy Button Not Working

**Problem**: Copy button doesn't copy URL to clipboard.

**Checklist**:

1. **Browser compatibility**: Clipboard API requires HTTPS or localhost
   ```
   ✓ http://localhost:8080 (works)
   ✓ https://monitor.example.com (works)
   ✗ http://monitor.example.com (may not work)
   ```

2. **Browser permissions**: Some browsers require user interaction
   - Clipboard access should work after clicking button
   - Check browser console for permission errors

3. **Manual copy workaround**:
   - Right-click URL text
   - Select "Copy"
   - Or triple-click URL to select, then Ctrl+C

---

### Example 15: Debug Business Hours False Alerts

**Problem**: Getting alerts at 8:01am when business hours start at 8:00am.

**Check your version**:
```bash
# This feature was added in v1.2.0
curl http://your-monitor:8080/api/v1/health | jq -r '.version'
```

**If running v1.2.0+**: Schedule-aware logic should prevent this.

**Debug checklist**:

1. **Verify schedule type**:
   ```bash
   curl http://your-monitor:8080/api/v1/hosts/myhost | jq -r '.schedule_type'
   # Should return: "business_hours"
   ```

2. **Check business hours configuration** (in .env or database):
   ```bash
   BUSINESS_HOURS_START=08:00
   BUSINESS_HOURS_END=18:00
   BUSINESS_HOURS_DAYS=1,2,3,4,5  # Mon-Fri
   BUSINESS_HOURS_TIMEZONE=America/Chicago
   ```

3. **Expected behavior**:
   - Last heartbeat: Friday 5:55pm
   - Monday 8:00am: Monitoring resumes
   - Frequency: 5 minutes
   - Grace: 60 seconds
   - **First possible alert**: Monday 8:00am + 5min + 60s = 8:06am

---

## Integration Examples

### Example 16: Integrate with Ansible

**Scenario**: Automatically register hosts via Ansible playbook.

```yaml
---
- name: Register host with monitoring system
  hosts: all
  tasks:
    - name: Register this host for heartbeat monitoring
      uri:
        url: "http://monitor:8080/api/v1/hosts"
        method: POST
        body_format: json
        body:
          name: "{{ inventory_hostname }}"
          expected_frequency_seconds: 300
          grace_period_seconds: 60
          schedule_type: "always"
        status_code: 200, 201
      register: monitor_response
      delegate_to: localhost
      run_once: false

    - name: Save heartbeat URL to host
      copy:
        content: "{{ monitor_response.json.heartbeat_url }}"
        dest: /etc/heartbeat_url
        mode: '0600'

    - name: Setup heartbeat cron job
      cron:
        name: "Send heartbeat to monitoring"
        minute: "*/5"
        job: "curl -s $(cat /etc/heartbeat_url) > /dev/null 2>&1"
```

---

### Example 17: Integrate with Terraform

**Scenario**: Register cloud infrastructure with monitoring during provisioning.

```hcl
# main.tf

resource "null_resource" "register_monitoring" {
  for_each = aws_instance.servers

  provisioner "local-exec" {
    command = <<-EOT
      curl -X POST http://monitor.internal:8080/api/v1/hosts \
        -H "Content-Type: application/json" \
        -d '{
          "name": "${each.value.tags.Name}",
          "expected_frequency_seconds": 300,
          "grace_period_seconds": 120,
          "schedule_type": "always"
        }' > /tmp/heartbeat_${each.key}.json
    EOT
  }

  provisioner "remote-exec" {
    inline = [
      "HEARTBEAT_URL=$(jq -r '.heartbeat_url' /tmp/heartbeat_${each.key}.json)",
      "echo \"*/5 * * * * curl -s $HEARTBEAT_URL\" | crontab -"
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("~/.ssh/id_rsa")
      host        = each.value.public_ip
    }
  }
}
```

---

### Example 18: Integrate with Prometheus AlertManager

**Scenario**: Send monitoring alerts to both Discord and AlertManager.

This would require custom development, but here's the concept:

```python
# In alert_service.py (custom modification)

def send_alert(self, alert_data):
    """Send alert to multiple destinations"""

    # Send to Discord (existing)
    self.send_discord_alert(alert_data)

    # Also send to AlertManager
    self.send_alertmanager_alert(alert_data)

def send_alertmanager_alert(self, alert_data):
    """Send alert to Prometheus AlertManager"""
    alertmanager_url = "http://alertmanager:9093/api/v1/alerts"

    payload = [{
        "labels": {
            "alertname": "HeartbeatMissing",
            "host": alert_data["host_name"],
            "severity": "critical"
        },
        "annotations": {
            "summary": alert_data["message"],
            "description": f"Host {alert_data['host_name']} missed heartbeat"
        }
    }]

    requests.post(alertmanager_url, json=payload)
```

---

## Best Practices

### Example 19: Production Deployment Best Practices

**1. Use HTTPS for external access**:
```nginx
# nginx reverse proxy
server {
    listen 443 ssl;
    server_name monitor.example.com;

    ssl_certificate /etc/ssl/certs/monitor.crt;
    ssl_certificate_key /etc/ssl/private/monitor.key;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**2. Backup database daily**:
```bash
#!/bin/bash
# /opt/scripts/backup-monitoring-db.sh

BACKUP_DIR="/backup/monitoring"
DB_PATH="/opt/network-monitoring/data/db.sqlite"
DATE=$(date +%Y%m%d-%H%M%S)

# Create backup
sqlite3 "$DB_PATH" ".backup ${BACKUP_DIR}/monitoring-${DATE}.db"

# Keep only last 30 days
find "$BACKUP_DIR" -name "monitoring-*.db" -mtime +30 -delete

# Crontab: 0 2 * * * /opt/scripts/backup-monitoring-db.sh
```

**3. Monitor the monitor**:
- Enable upstream monitoring to healthchecks.io
- Set up alerts if upstream heartbeat fails
- Use separate alerting channel (email, SMS) for meta-monitoring

**4. Document your setup**:
```bash
# /opt/network-monitoring/HOSTS.md

# Monitored Hosts

## Production Servers
- web-01: Every 5 minutes, 24/7
- web-02: Every 5 minutes, 24/7
- db-primary: Every 10 minutes, 24/7

## Backup Jobs
- nightly-backup: Once daily at 2am, business hours monitoring
- weekly-backup: Sundays at 3am, weekends only

## Services
- nginx-cluster: Every 5 minutes per node
- redis-cache: Every 2 minutes
```

---

## Summary

These examples cover:
- ✅ Basic cron job monitoring
- ✅ Business hours scheduling
- ✅ Docker/Kubernetes integration
- ✅ Systemd service monitoring
- ✅ Python application integration
- ✅ Multiple services on one host
- ✅ Remote site connectivity monitoring
- ✅ Browser testing
- ✅ Automated testing
- ✅ Runtime configuration (upstream, webhook)
- ✅ Troubleshooting common issues
- ✅ Infrastructure as Code integration (Ansible, Terraform)
- ✅ Production best practices

The key takeaway: **Copy the heartbeat URL from the UI and paste it anywhere you can run curl or HTTP GET**. That's all you need!
