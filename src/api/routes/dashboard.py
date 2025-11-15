"""Dashboard API endpoints."""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from src.database import Alert, Host, get_db
from src.database.schemas import DashboardResponse, HostStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/dashboard/data")
async def get_dashboard_data(db: Session = Depends(get_db)):
    """
    Get dashboard data (hosts status and recent alerts).

    Args:
        db: Database session

    Returns:
        Dashboard data with host details
    """
    # Get all hosts
    hosts = db.query(Host).all()

    # Build heartbeat URLs
    from src.config import get_settings
    settings = get_settings()

    host_details = []
    for host in hosts:
        heartbeat_url = f"http://{settings.api_host}:{settings.api_port}/api/v1/heartbeat/{host.host_id}?token={host.token}"
        host_details.append({
            "id": host.id,
            "name": host.name,
            "host_id": host.host_id,
            "status": host.status,
            "last_seen": host.last_seen.isoformat() if host.last_seen else None,
            "is_overdue": host.is_overdue(),
            "heartbeat_url": heartbeat_url,
            "cron_expression": host.cron_expression,
            "expected_frequency_seconds": host.expected_frequency_seconds,
        })

    # Count by status
    total_hosts = len(hosts)
    hosts_up = sum(1 for h in hosts if h.status == "up")
    hosts_down = sum(1 for h in hosts if h.status == "down")
    hosts_unknown = sum(1 for h in hosts if h.status == "unknown")

    # Get recent alerts (last 10)
    recent_alerts = (
        db.query(Alert).order_by(Alert.created_at.desc()).limit(10).all()
    )

    alert_data = [
        {
            "id": alert.id,
            "host_id": alert.host_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "acknowledged": alert.acknowledged,
            "created_at": alert.created_at.isoformat(),
        }
        for alert in recent_alerts
    ]

    return {
        "hosts": host_details,
        "recent_alerts": alert_data,
        "total_hosts": total_hosts,
        "hosts_up": hosts_up,
        "hosts_down": hosts_down,
        "hosts_unknown": hosts_unknown,
        "last_updated": datetime.utcnow().isoformat(),
    }


@router.get("/dashboard")
async def get_dashboard_html():
    """
    Serve simple HTML dashboard.

    Returns:
        HTML dashboard page
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Network Monitoring Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
            }

            header {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            header .header-content {
                flex: 1;
            }

            h1 {
                color: #333;
                font-size: 2em;
                margin-bottom: 10px;
            }

            .config-button {
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 1em;
                font-weight: 600;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                transition: background 0.3s;
            }

            .config-button:hover {
                background: #5568d3;
            }

            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }

            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }

            .stat-card h3 {
                color: #666;
                font-size: 0.9em;
                margin-bottom: 10px;
                text-transform: uppercase;
            }

            .stat-card .value {
                font-size: 2.5em;
                font-weight: bold;
            }

            .stat-card.up .value { color: #10b981; }
            .stat-card.down .value { color: #ef4444; }
            .stat-card.unknown .value { color: #f59e0b; }

            .hosts-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }

            .host-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border-left: 4px solid #ccc;
            }

            .host-card.up { border-left-color: #10b981; }
            .host-card.down { border-left-color: #ef4444; }
            .host-card.unknown { border-left-color: #f59e0b; }

            .host-card h3 {
                font-size: 1.2em;
                margin-bottom: 10px;
                color: #333;
            }

            .host-card .host-id {
                color: #666;
                font-size: 0.9em;
                margin-bottom: 15px;
            }

            .host-card .status {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: bold;
                text-transform: uppercase;
            }

            .status.up {
                background: #d1fae5;
                color: #047857;
            }

            .status.down {
                background: #fee2e2;
                color: #b91c1c;
            }

            .status.unknown {
                background: #fef3c7;
                color: #92400e;
            }

            .last-seen {
                color: #666;
                font-size: 0.85em;
                margin-top: 10px;
            }

            .alerts {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }

            .alerts h2 {
                color: #333;
                margin-bottom: 20px;
            }

            .alert-item {
                padding: 15px;
                border-left: 4px solid #ccc;
                margin-bottom: 15px;
                background: #f9fafb;
                border-radius: 5px;
            }

            .alert-item.critical { border-left-color: #ef4444; }
            .alert-item.warning { border-left-color: #f59e0b; }
            .alert-item.info { border-left-color: #3b82f6; }

            .alert-item .alert-message {
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }

            .alert-item .alert-time {
                color: #666;
                font-size: 0.85em;
            }

            .loading {
                text-align: center;
                padding: 40px;
                color: white;
                font-size: 1.2em;
            }

            .error {
                background: #fee2e2;
                color: #b91c1c;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }

            .refresh-info {
                color: white;
                text-align: center;
                margin-top: 20px;
                font-size: 0.9em;
            }

            .summary-table-container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 30px;
                overflow-x: auto;
            }

            .summary-table-container h2 {
                color: #333;
                margin-bottom: 20px;
            }

            .summary-table {
                width: 100%;
                border-collapse: collapse;
            }

            .summary-table th {
                background: #f3f4f6;
                padding: 12px;
                text-align: left;
                font-weight: 600;
                color: #374151;
                border-bottom: 2px solid #e5e7eb;
            }

            .summary-table td {
                padding: 12px;
                border-bottom: 1px solid #e5e7eb;
                color: #4b5563;
            }

            .summary-table tr:hover {
                background: #f9fafb;
            }

            .summary-table .url-cell {
                font-family: monospace;
                font-size: 0.85em;
                max-width: 300px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .summary-table .frequency-cell {
                font-family: monospace;
                font-size: 0.9em;
            }

            .summary-table .status-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: 600;
                text-transform: uppercase;
            }

            .summary-table .status-badge.up {
                background: #d1fae5;
                color: #047857;
            }

            .summary-table .status-badge.down {
                background: #fee2e2;
                color: #b91c1c;
            }

            .summary-table .status-badge.unknown {
                background: #fef3c7;
                color: #92400e;
            }

            .copy-button {
                background: #667eea;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 0.8em;
                cursor: pointer;
                margin-left: 8px;
                transition: background 0.2s;
            }

            .copy-button:hover {
                background: #5568d3;
            }

            .copy-button:active {
                background: #4a5bb8;
            }

            .copy-button.copied {
                background: #10b981;
            }

            .url-container {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .url-text {
                font-family: monospace;
                font-size: 0.85em;
                flex: 1;
                min-width: 0;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div class="header-content">
                    <h1>🖥️ Network Monitoring Dashboard</h1>
                    <p id="last-update">Loading...</p>
                </div>
                <a href="/api/v1/config" class="config-button">⚙️ Configuration</a>
            </header>

            <div class="stats">
                <div class="stat-card">
                    <h3>Total Hosts</h3>
                    <div class="value" id="total-hosts">-</div>
                </div>
                <div class="stat-card up">
                    <h3>Hosts Up</h3>
                    <div class="value" id="hosts-up">-</div>
                </div>
                <div class="stat-card down">
                    <h3>Hosts Down</h3>
                    <div class="value" id="hosts-down">-</div>
                </div>
                <div class="stat-card unknown">
                    <h3>Unknown Status</h3>
                    <div class="value" id="hosts-unknown">-</div>
                </div>
            </div>

            <div class="summary-table-container">
                <h2>📋 Monitored Hosts Summary</h2>
                <table class="summary-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Heartbeat URL</th>
                            <th>Frequency</th>
                            <th>Last Ping</th>
                        </tr>
                    </thead>
                    <tbody id="summary-table-body">
                        <tr><td colspan="5" style="text-align: center; color: #666;">Loading...</td></tr>
                    </tbody>
                </table>
            </div>

            <div id="hosts-container" class="hosts-grid"></div>

            <div class="alerts">
                <h2>📢 Recent Alerts</h2>
                <div id="alerts-container"></div>
            </div>

            <div class="refresh-info">
                Auto-refreshing every 30 seconds
            </div>
        </div>

        <script>
            function formatLastSeen(lastSeenStr) {
                if (!lastSeenStr) return 'Never';

                const lastSeen = new Date(lastSeenStr);
                const now = new Date();
                const diffMs = now - lastSeen;
                const diffMins = Math.floor(diffMs / 60000);
                const diffHours = Math.floor(diffMs / 3600000);
                const diffDays = Math.floor(diffMs / 86400000);

                if (diffMins < 1) return 'Just now';
                if (diffMins < 60) return `${diffMins}m ago`;
                if (diffHours < 24) return `${diffHours}h ago`;
                return `${diffDays}d ago`;
            }

            function formatFrequency(host) {
                if (host.cron_expression) {
                    return host.cron_expression;
                }
                const minutes = Math.floor(host.expected_frequency_seconds / 60);
                if (minutes < 60) {
                    return `Every ${minutes}m`;
                }
                const hours = Math.floor(minutes / 60);
                return `Every ${hours}h`;
            }

            function copyToClipboard(text, button) {
                navigator.clipboard.writeText(text).then(() => {
                    const originalText = button.textContent;
                    button.textContent = '✓ Copied!';
                    button.classList.add('copied');

                    setTimeout(() => {
                        button.textContent = originalText;
                        button.classList.remove('copied');
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy:', err);
                    alert('Failed to copy to clipboard');
                });
            }

            async function fetchDashboardData() {
                try {
                    const response = await fetch('/api/v1/dashboard/data');
                    const data = await response.json();
                    updateDashboard(data);
                } catch (error) {
                    console.error('Error fetching dashboard data:', error);
                    document.getElementById('hosts-container').innerHTML =
                        '<div class="error">Error loading dashboard data. Please check the server.</div>';
                    document.getElementById('summary-table-body').innerHTML =
                        '<tr><td colspan="5" style="text-align: center; color: #ef4444;">Error loading data</td></tr>';
                }
            }

            function updateDashboard(data) {
                // Update stats
                document.getElementById('total-hosts').textContent = data.total_hosts;
                document.getElementById('hosts-up').textContent = data.hosts_up;
                document.getElementById('hosts-down').textContent = data.hosts_down;
                document.getElementById('hosts-unknown').textContent = data.hosts_unknown;
                document.getElementById('last-update').textContent =
                    `Last updated: ${new Date(data.last_updated).toLocaleString()}`;

                // Update summary table
                const summaryTableBody = document.getElementById('summary-table-body');
                if (data.hosts.length === 0) {
                    summaryTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #666;">No hosts configured</td></tr>';
                } else {
                    summaryTableBody.innerHTML = data.hosts.map(host => `
                        <tr>
                            <td><strong>${host.name}</strong></td>
                            <td><span class="status-badge ${host.status}">${host.status}</span></td>
                            <td>
                                <div class="url-container">
                                    <span class="url-text" title="${host.heartbeat_url}">${host.heartbeat_url}</span>
                                    <button class="copy-button" data-url="${host.heartbeat_url}">📋 Copy</button>
                                </div>
                            </td>
                            <td class="frequency-cell">${formatFrequency(host)}</td>
                            <td>${formatLastSeen(host.last_seen)}</td>
                        </tr>
                    `).join('');

                    // Attach click handlers to copy buttons
                    document.querySelectorAll('.copy-button').forEach(button => {
                        button.addEventListener('click', function() {
                            const url = this.getAttribute('data-url');
                            copyToClipboard(url, this);
                        });
                    });
                }

                // Update hosts
                const hostsContainer = document.getElementById('hosts-container');
                hostsContainer.innerHTML = data.hosts.map(host => `
                    <div class="host-card ${host.status}">
                        <h3>${host.name}</h3>
                        <div class="host-id">${host.host_id}</div>
                        <span class="status ${host.status}">${host.status}</span>
                        <div class="last-seen">
                            ${host.last_seen
                                ? `Last seen: ${formatLastSeen(host.last_seen)}`
                                : 'Never seen'}
                        </div>
                        ${host.is_overdue ? '<div class="last-seen" style="color: #ef4444; font-weight: bold;">⚠️ Overdue</div>' : ''}
                    </div>
                `).join('');

                // Update alerts
                const alertsContainer = document.getElementById('alerts-container');
                if (data.recent_alerts.length === 0) {
                    alertsContainer.innerHTML = '<p style="color: #666;">No recent alerts</p>';
                } else {
                    alertsContainer.innerHTML = data.recent_alerts.map(alert => `
                        <div class="alert-item ${alert.severity}">
                            <div class="alert-message">${alert.message}</div>
                            <div class="alert-time">
                                ${new Date(alert.created_at).toLocaleString()} - ${alert.alert_type}
                            </div>
                        </div>
                    `).join('');
                }
            }

            // Initial load
            fetchDashboardData();

            // Refresh every 30 seconds
            setInterval(fetchDashboardData, 30000);
        </script>
    </body>
    </html>
    """

    return Response(content=html_content, media_type="text/html")
