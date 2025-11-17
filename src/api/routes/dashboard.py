"""Dashboard API endpoints."""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from src.database import Alert, Host, get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/dashboard/data")
async def get_dashboard_data(db: Session = Depends(get_db)):
    """Return host status summary and recent alerts for dashboard cards."""
    hosts = db.query(Host).all()

    from src.config import get_settings

    settings = get_settings()
    host_details = []
    for host in hosts:
        heartbeat_url = (
            f"http://{settings.api_host}:{settings.api_port}/api/v1/heartbeat/"
            f"{host.host_id}?token={host.token}"
        )
        host_details.append(
            {
                "id": host.id,
                "name": host.name,
                "host_id": host.host_id,
                "status": host.status,
                "last_seen": host.last_seen.isoformat() if host.last_seen else None,
                "is_overdue": host.is_overdue(),
                "heartbeat_url": heartbeat_url,
                "cron_expression": host.cron_expression,
                "expected_frequency_seconds": host.expected_frequency_seconds,
            }
        )

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
        "total_hosts": len(hosts),
        "hosts_up": sum(1 for h in hosts if h.status == "up"),
        "hosts_down": sum(1 for h in hosts if h.status == "down"),
        "hosts_unknown": sum(1 for h in hosts if h.status == "unknown"),
        "last_updated": datetime.utcnow().isoformat(),
    }


@router.get("/dashboard")
async def get_dashboard_html():
    """Serve the dashboard HTML that now includes the agent monitoring tab."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Network Monitoring Dashboard</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs/loader.min.js"></script>
        <style>
            :root {
                --font-sans: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
                --font-mono: "JetBrains Mono", Menlo, Monaco, Consolas, monospace;
                --radius: 0.75rem;
                --background: #f5f7fb;
                --foreground: #0f172a;
                --card: #ffffff;
                --primary: #2563eb;
                --primary-foreground: #f8fafc;
                --secondary: #e2e8f0;
                --muted-foreground: #475569;
                --border: #e2e8f0;
                --sidebar: #ffffff;
                --sidebar-foreground: #0f172a;
            }
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: var(--font-sans);
                background: var(--background);
                padding: 20px;
                min-height: 100vh;
                color: var(--foreground);
                font-feature-settings: "rlig" 1, "calt" 1;
            }
            .dashboard-shell {
                max-width: 1600px;
                margin: 0 auto;
                display: flex;
                gap: 20px;
            }
            .sidebar {
                width: 260px;
                background: var(--sidebar);
                border-radius: var(--radius);
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                padding: 20px;
                height: calc(100vh - 40px);
                position: sticky;
                top: 20px;
                display: flex;
                flex-direction: column;
                gap: 24px;
                border: 1px solid var(--border);
            }
            .sidebar h2 {
                font-size: 1.1em;
                color: var(--sidebar-foreground);
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
            }
            .sidebar-section h3 {
                font-size: 0.8em;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: var(--muted-foreground);
                margin-bottom: 8px;
                font-weight: 600;
            }
            .tab-button {
                width: 100%;
                border: none;
                border-radius: var(--radius);
                padding: 10px 12px;
                font-size: 0.95em;
                font-weight: 600;
                text-align: left;
                background: var(--secondary);
                color: var(--muted-foreground);
                cursor: pointer;
                transition: background 0.2s, color 0.2s;
            }
            .tab-button + .tab-button { margin-top: 10px; }
            .tab-button.active { background: var(--primary); color: var(--primary-foreground); }
            .tab-button:hover { background: #e0e7ff; }
            .quick-action {
                display: inline-block;
                width: 100%;
                text-align: center;
                padding: 10px 12px;
                border-radius: var(--radius);
                background: #10b981;
                color: white;
                text-decoration: none;
                font-weight: 600;
            }
            .quick-action:hover { background: #059669; }
            .content-container { flex: 1; }
            header {
                background: var(--card);
                padding: 30px;
                border-radius: var(--radius);
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                border: 1px solid var(--border);
                margin-bottom: 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            header .header-content { flex: 1; }
            h1 { color: var(--foreground); font-size: 2em; margin-bottom: 10px; }
            .config-button {
                background: var(--primary);
                color: var(--primary-foreground);
                border: none;
                padding: 12px 24px;
                border-radius: var(--radius);
                font-size: 1em;
                font-weight: 600;
                text-decoration: none;
                display: inline-block;
            }
            .config-button:hover { background: #1d4ed8; }
            .tab-view { display: none; }
            .tab-view.active { display: block; }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: var(--card);
                padding: 20px;
                border-radius: var(--radius);
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                border: 1px solid var(--border);
            }
            .stat-card h3 {
                color: var(--muted-foreground);
                font-size: 0.9em;
                margin-bottom: 10px;
                text-transform: uppercase;
            }
            .stat-card .value { font-size: 2.5em; font-weight: bold; }
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
                background: var(--card);
                padding: 20px;
                border-radius: var(--radius);
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                border: 1px solid var(--border);
                border-left: 4px solid var(--border);
            }
            .host-card.up { border-left-color: #10b981; }
            .host-card.down { border-left-color: #ef4444; }
            .host-card.unknown { border-left-color: #f59e0b; }
            .host-card h3 { font-size: 1.2em; margin-bottom: 10px; color: var(--foreground); }
            .host-id { color: var(--muted-foreground); font-size: 0.9em; margin-bottom: 12px; }
            .status {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 700;
                text-transform: uppercase;
            }
            .status.up { background: #d1fae5; color: #047857; }
            .status.down { background: #fee2e2; color: #b91c1c; }
            .status.unknown { background: #fef3c7; color: #92400e; }
            .last-seen { color: var(--muted-foreground); font-size: 0.85em; margin-top: 10px; }
            .alerts {
                background: var(--card);
                padding: 30px;
                border-radius: var(--radius);
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                border: 1px solid var(--border);
            }
            .alerts h2 { color: var(--foreground); margin-bottom: 20px; }
            .alert-item {
                padding: 15px;
                border-left: 4px solid var(--border);
                margin-bottom: 15px;
                background: var(--background);
                border-radius: var(--radius);
            }
            .alert-item.critical { border-left-color: #ef4444; }
            .alert-item.warning { border-left-color: #f59e0b; }
            .alert-item.info { border-left-color: #3b82f6; }
            .alert-message { font-weight: 600; color: var(--foreground); margin-bottom: 6px; }
            .alert-time { color: var(--muted-foreground); font-size: 0.85em; }
            .summary-table-container {
                background: var(--card);
                padding: 30px;
                border-radius: var(--radius);
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                border: 1px solid var(--border);
                margin-bottom: 30px;
                overflow-x: auto;
            }
            .summary-table { width: 100%; border-collapse: collapse; }
            .summary-table th {
                background: var(--secondary);
                padding: 12px;
                text-align: left;
                font-weight: 600;
                color: var(--foreground);
                border-bottom: 2px solid var(--border);
            }
            .summary-table td {
                padding: 12px;
                border-bottom: 1px solid var(--border);
                color: var(--muted-foreground);
            }
            .summary-table tr:hover { background: var(--background); }
            .status-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 999px;
                font-size: 0.8em;
                font-weight: 700;
                text-transform: uppercase;
            }
            .status-badge.up { background: #d1fae5; color: #047857; }
            .status-badge.down { background: #fee2e2; color: #b91c1c; }
            .status-badge.unknown { background: #fef3c7; color: #92400e; }
            .copy-button {
                background: var(--primary);
                color: var(--primary-foreground);
                border: none;
                padding: 6px 12px;
                border-radius: var(--radius);
                font-size: 0.8em;
                cursor: pointer;
                margin-left: 8px;
            }
            .copy-button.copied { background: #10b981; }
            .url-container { display: flex; align-items: center; gap: 8px; }
            .url-text {
                font-family: monospace;
                font-size: 0.85em;
                flex: 1;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .agent-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            .agent-panels {
                display: grid;
                grid-template-columns: 320px 1fr;
                gap: 20px;
                height: 860px;
                min-height: 860px;
            }
            .agent-list {
                background: var(--card);
                border-radius: var(--radius);
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                border: 1px solid var(--border);
                padding: 10px;
                height: 100%;
                overflow-y: auto;
            }
            .agent-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 14px 12px;
                border-radius: var(--radius);
                cursor: pointer;
                transition: background 0.15s;
            }
            .agent-item:hover { background: var(--secondary); }
            .agent-item.selected { background: #e0e7ff; border-left: 4px solid var(--primary); }
            .agent-name { font-weight: 600; color: var(--foreground); font-size: 0.95em; }
            .status-chip {
                padding: 4px 10px;
                border-radius: 999px;
                font-size: 0.75em;
                font-weight: 700;
                text-transform: uppercase;
            }
            .status-chip.active { background: #d1fae5; color: #047857; }
            .status-chip.idle { background: #fef9c3; color: #92400e; }
            .status-chip.not_running { background: #fee2e2; color: #b91c1c; }
            .agent-details {
                background: var(--card);
                border-radius: var(--radius);
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                border: 1px solid var(--border);
                padding: 20px;
                height: 100%;
                display: flex;
                flex-direction: column;
            }
            .agent-detail-card {
                flex: 1;
                display: flex;
                flex-direction: column;
                min-height: 0;
                height: 100%;
            }
            .agent-detail-header {
                flex-shrink: 0;
                display: flex;
                justify-content: space-between;
                gap: 20px;
                margin-bottom: 15px;
            }
            .editor-wrapper {
                flex: 1;
                display: flex;
                flex-direction: column;
                min-height: 0;
                overflow: hidden;
            }
            #monaco-editor-container {
                flex: 1;
                min-height: 0;
                border-radius: var(--radius);
                border: 1px solid var(--border);
                overflow: hidden;
            }
            .agent-actions {
                margin-top: 12px;
                display: flex;
                align-items: center;
                gap: 12px;
                flex-shrink: 0;
            }
            .save-button, .refresh-button {
                background: var(--primary);
                color: var(--primary-foreground);
                border: none;
                padding: 10px 18px;
                border-radius: var(--radius);
                font-weight: 600;
                cursor: pointer;
            }
            .save-button:disabled { opacity: 0.6; cursor: not-allowed; }
            .save-button:hover:not(:disabled), .refresh-button:hover { background: #1d4ed8; }
            .placeholder {
                color: var(--muted-foreground);
                text-align: center;
                padding: 40px;
            }
            .error-card {
                background: #fee2e2;
                color: #b91c1c;
                padding: 20px;
                border-radius: var(--radius);
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="dashboard-shell">
            <aside class="sidebar">
                <div>
                    <h2>📋 Views</h2>
                    <button class="tab-button active" data-tab="hosts" onclick="switchTab('hosts')">Network Dashboard</button>
                    <button class="tab-button" data-tab="agents" onclick="switchTab('agents')">Agent Jobs</button>
                </div>
                <div class="sidebar-section">
                    <h3>⚡ Quick Actions</h3>
                    <a href="/api/v1/config" class="quick-action">Open Configuration</a>
                </div>
            </aside>
            <main class="content-container">
                <header>
                    <div class="header-content">
                        <h1>🖥️ Network Monitoring Dashboard</h1>
                        <p id="last-update">Loading...</p>
                    </div>
                    <a href="/api/v1/config" class="config-button">⚙️ Configuration</a>
                </header>

                <section id="hosts-view" class="tab-view active">
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
                </section>

                <section id="agents-view" class="tab-view">
                    <div class="agent-header">
                        <div>
                            <h2>🤖 Agent Job Monitoring</h2>
                            <p style="color:#4b5563;">Review TASKS.md progress and Claude session activity.</p>
                        </div>
                        <button class="refresh-button" onclick="fetchAgentData(true)">Refresh</button>
                    </div>
                    <div class="agent-panels">
                        <div class="agent-list" id="agent-list">
                            <div class="placeholder">Loading agent projects...</div>
                        </div>
                        <div class="agent-details" id="agent-details">
                            <div class="placeholder">Select a project to view and edit its TASKS.md file.</div>
                        </div>
                    </div>
                </section>
            </main>
        </div>

        <script>
            const tabButtons = document.querySelectorAll('.tab-button[data-tab]');
            function switchTab(tab) {
                document.querySelectorAll('.tab-view').forEach(view => {
                    view.classList.toggle('active', view.id === `${tab}-view`);
                });
                tabButtons.forEach(button => {
                    button.classList.toggle('active', button.dataset.tab === tab);
                });
            }

            function formatLastSeen(lastSeenStr) {
                if (!lastSeenStr) return 'Never';
                const lastSeen = new Date(lastSeenStr);
                const diffMs = Date.now() - lastSeen.getTime();
                const diffMins = Math.floor(diffMs / 60000);
                if (diffMins < 1) return 'Just now';
                if (diffMins < 60) return `${diffMins}m ago`;
                const diffHours = Math.floor(diffMins / 60);
                if (diffHours < 24) return `${diffHours}h ago`;
                return `${Math.floor(diffHours / 24)}d ago`;
            }

            function formatFrequency(host) {
                if (host.cron_expression) return host.cron_expression;
                const minutes = Math.floor(host.expected_frequency_seconds / 60);
                if (minutes < 60) return `Every ${minutes}m`;
                return `Every ${Math.floor(minutes / 60)}h`;
            }

            function copyToClipboard(text, button) {
                navigator.clipboard.writeText(text).then(() => {
                    const original = button.textContent;
                    button.textContent = '✓ Copied!';
                    button.classList.add('copied');
                    setTimeout(() => {
                        button.textContent = original;
                        button.classList.remove('copied');
                    }, 2000);
                }).catch(err => {
                    console.error('Clipboard error', err);
                    alert('Failed to copy to clipboard');
                });
            }

            async function fetchDashboardData() {
                try {
                    const response = await fetch('/api/v1/dashboard/data');
                    updateDashboard(await response.json());
                } catch (error) {
                    console.error('Error fetching dashboard data', error);
                    document.getElementById('hosts-container').innerHTML = '<div class="error-card">Failed to load host data.</div>';
                }
            }

            function updateDashboard(data) {
                document.getElementById('total-hosts').textContent = data.total_hosts;
                document.getElementById('hosts-up').textContent = data.hosts_up;
                document.getElementById('hosts-down').textContent = data.hosts_down;
                document.getElementById('hosts-unknown').textContent = data.hosts_unknown;
                document.getElementById('last-update').textContent = `Last updated: ${new Date(data.last_updated).toLocaleString()}`;

                const summaryBody = document.getElementById('summary-table-body');
                summaryBody.innerHTML = data.hosts.length === 0 ?
                    '<tr><td colspan="5" style="text-align:center; color:#666;">No hosts configured</td></tr>' :
                    data.hosts.map(host => `
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
                document.querySelectorAll('.copy-button').forEach(btn => btn.addEventListener('click', () => copyToClipboard(btn.dataset.url, btn)));

                document.getElementById('hosts-container').innerHTML = data.hosts.map(host => `
                    <div class="host-card ${host.status}">
                        <h3>${host.name}</h3>
                        <div class="host-id">${host.host_id}</div>
                        <span class="status ${host.status}">${host.status}</span>
                        <div class="last-seen">${host.last_seen ? `Last seen: ${formatLastSeen(host.last_seen)}` : 'Never seen'}</div>
                        ${host.is_overdue ? '<div class="last-seen" style="color:#ef4444; font-weight:700;">⚠️ Overdue</div>' : ''}
                    </div>
                `).join('');

                document.getElementById('alerts-container').innerHTML = data.recent_alerts.length === 0 ?
                    '<p style="color:#666;">No recent alerts</p>' :
                    data.recent_alerts.map(alert => `
                        <div class="alert-item ${alert.severity}">
                            <div class="alert-message">${alert.message}</div>
                            <div class="alert-time">${new Date(alert.created_at).toLocaleString()} — ${alert.alert_type}</div>
                        </div>
                    `).join('');
            }

            const agentListEl = document.getElementById('agent-list');
            const agentDetailsEl = document.getElementById('agent-details');
            let agentsCache = [];
            let selectedAgent = null;
            let monacoEditor = null;

            function statusLabel(status) {
                return status ? status.replace(/_/g, ' ') : 'unknown';
            }

            function relativeTimestamp(epochSeconds) {
                if (!epochSeconds) return 'N/A';
                const diffMs = Date.now() - epochSeconds * 1000;
                const mins = Math.floor(diffMs / 60000);
                if (mins < 1) return 'just now';
                if (mins < 60) return `${mins}m ago`;
                const hours = Math.floor(mins / 60);
                if (hours < 24) return `${hours}h ago`;
                return `${Math.floor(hours / 24)}d ago`;
            }

            function renderAgentList() {
                if (!agentsCache.length) {
                    agentListEl.innerHTML = '<div class="placeholder">No docs/TASKS.md files found.</div>';
                    return;
                }
                agentListEl.innerHTML = agentsCache.map(agent => `
                    <div class="agent-item ${agent.name === selectedAgent ? 'selected' : ''}" data-agent="${agent.name}">
                        <div>
                            <div class="agent-name">${agent.name}</div>
                        </div>
                        <span class="status-chip ${agent.status}">${statusLabel(agent.status)}</span>
                    </div>
                `).join('');
                agentListEl.querySelectorAll('.agent-item').forEach(item => {
                    item.addEventListener('click', () => loadAgentDetails(item.dataset.agent));
                });
            }

            async function fetchAgentData(showSpinner = false) {
                if (showSpinner) {
                    agentListEl.innerHTML = '<div class="placeholder">Refreshing agent list...</div>';
                }
                try {
                    const response = await fetch('/api/v1/agents');
                    const data = await response.json();
                    agentsCache = data.projects || [];
                    renderAgentList();
                } catch (error) {
                    console.error('Error fetching agents', error);
                    agentListEl.innerHTML = '<div class="error-card">Failed to load agent data.</div>';
                }
            }

            async function loadAgentDetails(agentName) {
                selectedAgent = agentName;
                renderAgentList();
                agentDetailsEl.innerHTML = '<div class="placeholder">Loading task file...</div>';
                try {
                    const response = await fetch(`/api/v1/agents/${encodeURIComponent(agentName)}`);
                    if (!response.ok) throw new Error('Failed to load agent');
                    renderAgentDetails(await response.json());
                } catch (error) {
                    console.error('Error loading agent detail', error);
                    agentDetailsEl.innerHTML = '<div class="error-card">Unable to load task file.</div>';
                }
            }

            function renderAgentDetails(agent) {
                agentDetailsEl.innerHTML = `
                    <div class="agent-detail-card">
                        <div class="agent-detail-header">
                            <div>
                                <h3 style="margin-bottom:6px;">${agent.name}</h3>
                                <div class="agent-meta">Project: ${agent.project_path}</div>
                                <div class="agent-meta">File: ${agent.tasks_file}</div>
                                <div class="agent-meta">File updated: ${relativeTimestamp(agent.file_mtime)}</div>
                            </div>
                            <div style="text-align:right;">
                                <span class="status-chip ${agent.status}">${statusLabel(agent.status)}</span>
                                <div class="agent-meta">Session: ${relativeTimestamp(agent.status_updated_at)}</div>
                            </div>
                        </div>
                        <div class="editor-wrapper">
                            <div id="monaco-editor-container"></div>
                        </div>
                        <div class="agent-actions">
                            <button class="save-button" id="agent-save-btn">Save Changes</button>
                            <span class="agent-meta" id="agent-save-status"></span>
                        </div>
                    </div>
                `;

                // Destroy previous editor instance if exists
                if (monacoEditor) {
                    monacoEditor.dispose();
                    monacoEditor = null;
                }

                // Initialize Monaco Editor
                require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' } });
                require(['vs/editor/editor.main'], function() {
                    monacoEditor = monaco.editor.create(document.getElementById('monaco-editor-container'), {
                        value: agent.contents,
                        language: 'markdown',
                        theme: 'vs',
                        automaticLayout: true,
                        minimap: { enabled: true },
                        wordWrap: 'on',
                        lineNumbers: 'on',
                        fontSize: 14,
                        scrollBeyondLastLine: false,
                        renderWhitespace: 'selection',
                        quickSuggestions: false,
                        folding: true,
                        links: true,
                        padding: { top: 10, bottom: 10 }
                    });
                });

                document.getElementById('agent-save-btn').addEventListener('click', () => saveAgentTasks(agent.name));
            }

            async function saveAgentTasks(agentName) {
                const statusEl = document.getElementById('agent-save-status');
                const button = document.getElementById('agent-save-btn');
                button.disabled = true;
                statusEl.textContent = 'Saving...';
                try {
                    const contents = monacoEditor ? monacoEditor.getValue() : '';
                    const response = await fetch(`/api/v1/agents/${encodeURIComponent(agentName)}`,
                        {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ contents: contents }),
                        });
                    if (!response.ok) throw new Error('Save failed');
                    statusEl.textContent = 'Saved!';
                    fetchAgentData();
                } catch (error) {
                    console.error('Error saving task file', error);
                    statusEl.textContent = 'Save failed';
                } finally {
                    button.disabled = false;
                    setTimeout(() => statusEl.textContent = '', 3000);
                }
            }

            fetchDashboardData();
            fetchAgentData();
            setInterval(fetchDashboardData, 30000);
            setInterval(fetchAgentData, 60000);
        </script>
    </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")
