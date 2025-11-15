"""Configuration viewer endpoints."""
import logging
from fastapi import APIRouter, Response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/config")
async def get_config_html():
    """
    Serve simple configuration viewer/editor page.

    Returns:
        HTML configuration page
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Host Configuration - Network Monitoring</title>
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

            h1 {
                color: #333;
                font-size: 2em;
                margin-bottom: 10px;
            }

            .header-left {
                flex: 1;
            }

            .header-right {
                display: flex;
                gap: 10px;
            }

            .add-host-btn {
                background: #10b981;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
                font-size: 1em;
            }

            .add-host-btn:hover {
                background: #059669;
            }

            .nav {
                margin-top: 15px;
            }

            .nav a {
                color: #667eea;
                text-decoration: none;
                margin-right: 20px;
                font-weight: 500;
            }

            .nav a:hover {
                text-decoration: underline;
            }

            .config-table {
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                overflow-x: auto;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                min-width: 1200px;
            }

            th {
                background: #f3f4f6;
                padding: 15px;
                text-align: left;
                font-weight: 600;
                color: #374151;
                border-bottom: 2px solid #e5e7eb;
            }

            td {
                padding: 15px;
                border-bottom: 1px solid #e5e7eb;
                color: #1f2937;
            }

            tr:hover {
                background: #f9fafb;
            }

            .status-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.85em;
                font-weight: 600;
            }

            .status-up {
                background: #d1fae5;
                color: #047857;
            }

            .status-down {
                background: #fee2e2;
                color: #b91c1c;
            }

            .status-unknown {
                background: #fef3c7;
                color: #92400e;
            }

            .schedule-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.85em;
                background: #e0e7ff;
                color: #3730a3;
            }

            .config-value {
                font-family: 'Courier New', monospace;
                color: #4b5563;
                font-size: 0.9em;
            }

            .url-value {
                font-family: 'Courier New', monospace;
                color: #6b7280;
                font-size: 0.8em;
                max-width: 300px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .loading {
                text-align: center;
                padding: 40px;
                color: #666;
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

            .edit-btn, .delete-btn {
                border: none;
                padding: 6px 12px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.85em;
                font-weight: 500;
                margin-right: 5px;
            }

            .edit-btn {
                background: #667eea;
                color: white;
            }

            .edit-btn:hover {
                background: #5568d3;
            }

            .delete-btn {
                background: #ef4444;
                color: white;
            }

            .delete-btn:hover {
                background: #dc2626;
            }

            .copy-url-btn {
                background: #10b981;
                color: white;
                border: none;
                padding: 4px 10px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.75em;
                margin-left: 8px;
                transition: background 0.2s;
            }

            .copy-url-btn:hover {
                background: #059669;
            }

            .copy-url-btn.copied {
                background: #3b82f6;
            }

            .url-container {
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .url-text {
                flex: 1;
                min-width: 0;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                z-index: 1000;
                align-items: center;
                justify-content: center;
                overflow-y: auto;
            }

            .modal.show {
                display: flex;
            }

            .modal-content {
                background: white;
                padding: 30px;
                border-radius: 10px;
                max-width: 600px;
                width: 90%;
                max-height: 90vh;
                overflow-y: auto;
            }

            .modal-content h2 {
                margin-bottom: 20px;
                color: #333;
            }

            .form-group {
                margin-bottom: 15px;
            }

            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: 500;
                color: #374151;
            }

            .form-group input, .form-group select {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 1em;
            }

            .form-group small {
                color: #6b7280;
                font-size: 0.85em;
            }

            .form-actions {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }

            .btn {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
                flex: 1;
            }

            .btn-primary {
                background: #667eea;
                color: white;
            }

            .btn-primary:hover {
                background: #5568d3;
            }

            .btn-secondary {
                background: #e5e7eb;
                color: #374151;
            }

            .btn-secondary:hover {
                background: #d1d5db;
            }

            .log-analysis-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-left: 8px;
            }

            .log-analysis-enabled {
                background: #10b981;
            }

            .log-analysis-disabled {
                background: #d1d5db;
            }

            .help-text {
                background: #eff6ff;
                border-left: 3px solid #3b82f6;
                padding: 10px;
                margin-top: 10px;
                font-size: 0.9em;
                color: #1e40af;
            }

            .cron-examples {
                margin-top: 5px;
                font-size: 0.85em;
                color: #6b7280;
            }

            .cron-examples code {
                background: #f3f4f6;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }

            .settings-section {
                background: white;
                padding: 25px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 25px;
            }

            .settings-section h2 {
                margin-bottom: 20px;
                color: #333;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .webhook-config {
                display: flex;
                gap: 15px;
                align-items: flex-end;
            }

            .webhook-config .form-group {
                flex: 1;
                margin-bottom: 0;
            }

            .webhook-config button {
                background: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: 600;
                height: 42px;
            }

            .webhook-config button:hover {
                background: #059669;
            }

            .webhook-status {
                margin-top: 10px;
                padding: 10px;
                border-radius: 5px;
                display: none;
            }

            .webhook-status.success {
                background: #d1fae5;
                color: #065f46;
                display: block;
            }

            .webhook-status.error {
                background: #fee2e2;
                color: #991b1b;
                display: block;
            }

            .upstream-config {
                margin-top: 25px;
                padding-top: 25px;
                border-top: 1px solid #e5e7eb;
            }

            .upstream-toggle {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 15px;
            }

            .upstream-toggle input[type="checkbox"] {
                width: 20px;
                height: 20px;
                cursor: pointer;
            }

            .upstream-toggle label {
                cursor: pointer;
                font-weight: 600;
                margin: 0;
            }

            .upstream-fields {
                display: grid;
                grid-template-columns: 2fr 1fr auto;
                gap: 15px;
                align-items: flex-end;
            }

            .upstream-fields button {
                background: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: 600;
                height: 42px;
            }

            .upstream-fields button:hover {
                background: #059669;
            }

            .upstream-fields button:disabled {
                background: #9ca3af;
                cursor: not-allowed;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div class="header-left">
                    <h1>⚙️ Host Configuration</h1>
                    <div class="nav">
                        <a href="/api/v1/dashboard">← Back to Dashboard</a>
                        <a href="/api/v1/health">System Health</a>
                        <a href="/docs">API Docs</a>
                    </div>
                </div>
                <div class="header-right">
                    <button class="add-host-btn" onclick="openAddModal()">+ Add Host</button>
                </div>
            </header>

            <!-- System Settings Section -->
            <div class="settings-section">
                <h2>🔔 Notification Settings</h2>
                <div class="webhook-config">
                    <div class="form-group">
                        <label>Discord Webhook URL</label>
                        <input type="url" id="webhook-url" placeholder="https://discord.com/api/webhooks/...">
                        <small id="webhook-source" style="color: #666;"></small>
                    </div>
                    <button onclick="saveWebhookUrl()">Save Webhook</button>
                </div>
                <div id="webhook-status" class="webhook-status"></div>

                <!-- Upstream Monitoring Section -->
                <div class="upstream-config">
                    <div class="upstream-toggle">
                        <input type="checkbox" id="upstream-enabled" onchange="toggleUpstreamFields()">
                        <label for="upstream-enabled">Enable Upstream Monitoring (Self-Monitoring)</label>
                    </div>
                    <p style="color: #666; font-size: 0.9em; margin-bottom: 15px;">
                        This hub will send heartbeats to an external service to confirm it's healthy.
                        Compatible with healthchecks.io, Uptime Kuma, and similar services.
                    </p>
                    <div class="upstream-fields">
                        <div class="form-group">
                            <label>Upstream Monitoring URL</label>
                            <input type="url" id="upstream-url" placeholder="https://hc-ping.com/your-uuid" disabled>
                            <small id="upstream-source" style="color: #666;"></small>
                        </div>
                        <div class="form-group">
                            <label>Frequency (seconds)</label>
                            <input type="number" id="upstream-frequency" min="60" value="300" disabled>
                        </div>
                        <button id="upstream-save-btn" onclick="saveUpstreamConfig()" disabled>Save Config</button>
                    </div>
                    <div id="upstream-status" class="webhook-status"></div>
                </div>
            </div>

            <div class="config-table">
                <table id="config-table">
                    <thead>
                        <tr>
                            <th>Host Name</th>
                            <th>Host ID</th>
                            <th>Status</th>
                            <th>Heartbeat URL</th>
                            <th>Frequency (Cron)</th>
                            <th>Grace Period</th>
                            <th>Schedule</th>
                            <th>Last Seen</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="config-tbody">
                        <tr>
                            <td colspan="9" class="loading">Loading configurations...</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="refresh-info">
                Auto-refreshing every 30 seconds
            </div>
        </div>

        <!-- Add Host Modal -->
        <div id="add-modal" class="modal">
            <div class="modal-content">
                <h2>Add New Host</h2>
                <form id="add-form">
                    <div class="form-group">
                        <label>Host Name *</label>
                        <input type="text" id="add-name" required>
                        <small>Display name for this host</small>
                    </div>

                    <div class="form-group">
                        <label>Host ID *</label>
                        <input type="text" id="add-host-id" required pattern="[a-zA-Z0-9_-]+">
                        <small>Unique identifier (alphanumeric, dashes, underscores)</small>
                    </div>

                    <div class="form-group">
                        <label>Heartbeat Frequency (Cron Expression) *</label>
                        <input type="text" id="add-cron" placeholder="*/5 * * * *" required>
                        <div class="cron-examples">
                            Examples:<br>
                            <code>*/5 * * * *</code> = Every 5 minutes<br>
                            <code>0 * * * *</code> = Every hour<br>
                            <code>0 0 * * *</code> = Daily at midnight<br>
                            <code>0 9-17 * * 1-5</code> = Every hour 9am-5pm, Mon-Fri
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Grace Period (seconds)</label>
                        <input type="number" id="add-grace" value="60" min="0" step="1">
                        <small>How long to wait before alerting after missed heartbeat</small>
                    </div>

                    <div class="form-group">
                        <label>Monitoring Schedule</label>
                        <select id="add-schedule">
                            <option value="always">Always (24/7)</option>
                            <option value="business_hours">Business Hours Only</option>
                        </select>
                    </div>

                    <div class="help-text">
                        A secure token will be automatically generated for this host.
                        After creation, you'll see the token and setup instructions.
                    </div>

                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" onclick="closeAddModal()">Cancel</button>
                        <button type="submit" class="btn btn-primary">Create Host</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Edit Modal -->
        <div id="edit-modal" class="modal">
            <div class="modal-content">
                <h2>Edit Host Configuration</h2>
                <form id="edit-form">
                    <input type="hidden" id="edit-host-id">

                    <div class="form-group">
                        <label>Host Name</label>
                        <input type="text" id="edit-name" disabled>
                    </div>

                    <div class="form-group">
                        <label>Heartbeat Frequency (Cron Expression)</label>
                        <input type="text" id="edit-cron" placeholder="*/5 * * * *">
                        <div class="cron-examples">
                            Current: <strong id="current-cron"></strong><br>
                            Leave blank to keep unchanged
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Grace Period (seconds)</label>
                        <input type="number" id="edit-grace" min="0" step="1">
                        <small style="color: #6b7280;">Current: <span id="current-grace"></span></small>
                    </div>

                    <div class="form-group">
                        <label>Monitoring Schedule</label>
                        <select id="edit-schedule">
                            <option value="always">Always (24/7)</option>
                            <option value="business_hours">Business Hours Only</option>
                        </select>
                        <small style="color: #6b7280;">Current: <span id="current-schedule"></span></small>
                    </div>

                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" onclick="closeEditModal()">Cancel</button>
                        <button type="submit" class="btn btn-primary">Save Changes</button>
                    </div>
                </form>
            </div>
        </div>

        <script>
            let currentConfigs = [];

            async function fetchConfigurations() {
                try {
                    const response = await fetch('/api/v1/hosts/config/all');
                    const data = await response.json();
                    currentConfigs = data.hosts;
                    updateTable(data.hosts);
                } catch (error) {
                    console.error('Error fetching configurations:', error);
                    document.getElementById('config-tbody').innerHTML =
                        '<tr><td colspan="9" class="error">Error loading configurations. Please check the server.</td></tr>';
                }
            }

            function formatLastSeen(lastSeenISO) {
                if (!lastSeenISO) return 'Never';
                const date = new Date(lastSeenISO);
                const now = new Date();
                const diffMs = now - date;
                const diffMins = Math.floor(diffMs / 60000);
                const diffHours = Math.floor(diffMins / 60);
                const diffDays = Math.floor(diffHours / 24);

                if (diffMins < 1) return 'Just now';
                if (diffMins < 60) return `${diffMins}m ago`;
                if (diffHours < 24) return `${diffHours}h ago`;
                return `${diffDays}d ago`;
            }

            function copyUrlToClipboard(url, button) {
                navigator.clipboard.writeText(url).then(() => {
                    const originalHTML = button.innerHTML;
                    button.innerHTML = '✓';
                    button.classList.add('copied');

                    setTimeout(() => {
                        button.innerHTML = originalHTML;
                        button.classList.remove('copied');
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy URL:', err);
                    alert('Failed to copy URL to clipboard');
                });
            }

            async function fetchWebhookConfig() {
                try {
                    const response = await fetch('/api/v1/settings/webhook');
                    const data = await response.json();

                    document.getElementById('webhook-url').value = data.webhook_url;

                    // Show source info
                    const sourceText = data.source === 'database' ?
                        '(configured in database)' :
                        data.source === 'environment' ?
                        '(from environment variable)' :
                        '(not configured)';
                    document.getElementById('webhook-source').textContent = sourceText;
                } catch (error) {
                    console.error('Error fetching webhook config:', error);
                }
            }

            async function saveWebhookUrl() {
                const webhookUrl = document.getElementById('webhook-url').value;
                const statusDiv = document.getElementById('webhook-status');

                if (!webhookUrl) {
                    statusDiv.className = 'webhook-status error';
                    statusDiv.textContent = 'Please enter a webhook URL';
                    return;
                }

                try {
                    const response = await fetch('/api/v1/settings/webhook', {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            webhook_url: webhookUrl
                        }),
                    });

                    if (response.ok) {
                        statusDiv.className = 'webhook-status success';
                        statusDiv.textContent = '✓ Webhook URL saved successfully!';
                        document.getElementById('webhook-source').textContent = '(configured in database)';

                        setTimeout(() => {
                            statusDiv.className = 'webhook-status';
                        }, 3000);
                    } else {
                        const error = await response.json();
                        statusDiv.className = 'webhook-status error';
                        statusDiv.textContent = `Error: ${error.detail || 'Failed to save webhook URL'}`;
                    }
                } catch (error) {
                    console.error('Error saving webhook URL:', error);
                    statusDiv.className = 'webhook-status error';
                    statusDiv.textContent = 'Error saving webhook URL. Please try again.';
                }
            }

            async function fetchUpstreamConfig() {
                try {
                    const response = await fetch('/api/v1/settings/upstream');
                    const data = await response.json();

                    document.getElementById('upstream-enabled').checked = data.enabled;
                    document.getElementById('upstream-url').value = data.url || '';
                    document.getElementById('upstream-frequency').value = data.frequency_seconds;

                    // Show source info
                    const sourceText = data.source === 'database' ?
                        '(configured in database)' :
                        data.source === 'environment' ?
                        '(from environment variable)' :
                        '(not configured)';
                    document.getElementById('upstream-source').textContent = sourceText;

                    // Enable/disable fields based on enabled state
                    toggleUpstreamFields();
                } catch (error) {
                    console.error('Error fetching upstream config:', error);
                }
            }

            function toggleUpstreamFields() {
                const enabled = document.getElementById('upstream-enabled').checked;
                document.getElementById('upstream-url').disabled = !enabled;
                document.getElementById('upstream-frequency').disabled = !enabled;
                document.getElementById('upstream-save-btn').disabled = !enabled;
            }

            async function saveUpstreamConfig() {
                const enabled = document.getElementById('upstream-enabled').checked;
                const url = document.getElementById('upstream-url').value;
                const frequency = parseInt(document.getElementById('upstream-frequency').value);
                const statusDiv = document.getElementById('upstream-status');

                if (enabled && !url) {
                    statusDiv.className = 'webhook-status error';
                    statusDiv.textContent = 'Please enter an upstream monitoring URL';
                    return;
                }

                if (frequency < 60) {
                    statusDiv.className = 'webhook-status error';
                    statusDiv.textContent = 'Frequency must be at least 60 seconds';
                    return;
                }

                try {
                    const response = await fetch('/api/v1/settings/upstream', {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            enabled: enabled,
                            url: url,
                            frequency_seconds: frequency
                        }),
                    });

                    if (response.ok) {
                        statusDiv.className = 'webhook-status success';
                        statusDiv.textContent = enabled ?
                            '✓ Upstream monitoring enabled and configured!' :
                            '✓ Upstream monitoring disabled';
                        document.getElementById('upstream-source').textContent = '(configured in database)';

                        setTimeout(() => {
                            statusDiv.className = 'webhook-status';
                        }, 3000);
                    } else {
                        const error = await response.json();
                        statusDiv.className = 'webhook-status error';
                        statusDiv.textContent = `Error: ${error.detail || 'Failed to save upstream config'}`;
                    }
                } catch (error) {
                    console.error('Error saving upstream config:', error);
                    statusDiv.className = 'webhook-status error';
                    statusDiv.textContent = 'Error saving upstream config. Please try again.';
                }
            }

            function updateTable(hosts) {
                const tbody = document.getElementById('config-tbody');

                if (hosts.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 40px; color: #9ca3af;">No hosts configured yet. Click "Add Host" to get started.</td></tr>';
                    return;
                }

                tbody.innerHTML = hosts.map(host => `
                    <tr>
                        <td><strong>${host.name}</strong></td>
                        <td class="config-value">${host.host_id}</td>
                        <td>
                            <span class="status-badge status-${host.status}">${host.status.toUpperCase()}</span>
                        </td>
                        <td class="url-value">
                            <div class="url-container">
                                <span class="url-text" title="${host.heartbeat_url}">${host.heartbeat_url}</span>
                                <button class="copy-url-btn" onclick="copyUrlToClipboard('${host.heartbeat_url}', this)">📋</button>
                            </div>
                        </td>
                        <td class="config-value">${host.cron_expression || 'N/A'}</td>
                        <td class="config-value">${host.grace_period_seconds}s</td>
                        <td>
                            <span class="schedule-badge">${host.schedule_type.replace('_', ' ').toUpperCase()}</span>
                        </td>
                        <td class="config-value">${formatLastSeen(host.last_seen)}</td>
                        <td>
                            <button class="edit-btn" onclick="openEditModal('${host.host_id}')">Edit</button>
                            <button class="delete-btn" onclick="deleteHost('${host.host_id}', '${host.name}')">Delete</button>
                        </td>
                    </tr>
                `).join('');
            }

            function openAddModal() {
                document.getElementById('add-modal').classList.add('show');
            }

            function closeAddModal() {
                document.getElementById('add-modal').classList.remove('show');
                document.getElementById('add-form').reset();
            }

            function openEditModal(hostId) {
                const host = currentConfigs.find(h => h.host_id === hostId);
                if (!host) return;

                document.getElementById('edit-host-id').value = hostId;
                document.getElementById('edit-name').value = host.name;
                document.getElementById('edit-cron').value = host.cron_expression || '';
                document.getElementById('edit-grace').value = host.grace_period_seconds;
                document.getElementById('edit-schedule').value = host.schedule_type;

                document.getElementById('current-cron').textContent = host.cron_expression || 'Not set';
                document.getElementById('current-grace').textContent = `${host.grace_period_seconds}s`;
                document.getElementById('current-schedule').textContent = host.schedule_type.replace('_', ' ');

                document.getElementById('edit-modal').classList.add('show');
            }

            function closeEditModal() {
                document.getElementById('edit-modal').classList.remove('show');
            }

            async function deleteHost(hostId, hostName) {
                if (!confirm(`Are you sure you want to delete host "${hostName}"?\\n\\nThis will remove all associated heartbeat records and alerts. This action cannot be undone.`)) {
                    return;
                }

                try {
                    const response = await fetch(`/api/v1/hosts/${hostId}`, {
                        method: 'DELETE',
                    });

                    if (response.ok) {
                        alert(`Host "${hostName}" deleted successfully!`);
                        fetchConfigurations(); // Refresh table
                    } else {
                        const error = await response.json();
                        alert(`Error: ${error.detail || 'Failed to delete host'}` );
                    }
                } catch (error) {
                    console.error('Error deleting host:', error);
                    alert('Error deleting host. Please try again.');
                }
            }

            document.getElementById('add-form').addEventListener('submit', async (e) => {
                e.preventDefault();

                const name = document.getElementById('add-name').value;
                const hostId = document.getElementById('add-host-id').value;
                const cronExpression = document.getElementById('add-cron').value;
                const graceSeconds = parseInt(document.getElementById('add-grace').value);
                const scheduleType = document.getElementById('add-schedule').value;

                try {
                    // Generate token
                    const tokenResponse = await fetch('/api/v1/hosts/generate-token', {
                        method: 'POST',
                    });
                    const tokenData = await tokenResponse.json();
                    const token = tokenData.token;

                    // Create host
                    const response = await fetch('/api/v1/hosts', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            name: name,
                            host_id: hostId,
                            token: token,
                            cron_expression: cronExpression,
                            expected_frequency_seconds: 300, // Default fallback
                            schedule_type: scheduleType,
                            grace_period_seconds: graceSeconds,
                        }),
                    });

                    if (response.ok) {
                        const result = await response.json();
                        closeAddModal();
                        fetchConfigurations(); // Refresh table

                        // Show success with token
                        alert(`Host created successfully!\\n\\nHost ID: ${hostId}\\nToken: ${token}\\nHeartbeat URL: ${result.heartbeat_url}\\n\\nSave this token securely - you'll need it to configure the client!`);
                    } else {
                        const error = await response.json();
                        alert(`Error: ${error.detail || 'Failed to create host'}`);
                    }
                } catch (error) {
                    console.error('Error creating host:', error);
                    alert('Error creating host. Please try again.');
                }
            });

            document.getElementById('edit-form').addEventListener('submit', async (e) => {
                e.preventDefault();

                const hostId = document.getElementById('edit-host-id').value;
                const cronExpression = document.getElementById('edit-cron').value;
                const graceSeconds = parseInt(document.getElementById('edit-grace').value);
                const schedule = document.getElementById('edit-schedule').value;

                // Build query params
                const params = new URLSearchParams();
                if (cronExpression) params.append('cron_expression', cronExpression);
                if (graceSeconds) params.append('grace_period_seconds', graceSeconds);
                if (schedule) params.append('schedule_type', schedule);

                if (params.toString() === '') {
                    alert('No changes to save');
                    return;
                }

                try {
                    const response = await fetch(`/api/v1/hosts/${hostId}/config?${params.toString()}`, {
                        method: 'PATCH',
                    });

                    if (response.ok) {
                        closeEditModal();
                        fetchConfigurations(); // Refresh table
                        alert('Configuration updated successfully!');
                    } else {
                        const error = await response.json();
                        alert(`Error: ${error.detail || 'Failed to update configuration'}`);
                    }
                } catch (error) {
                    console.error('Error updating configuration:', error);
                    alert('Error updating configuration. Please try again.');
                }
            });

            // Initial load
            fetchConfigurations();
            fetchWebhookConfig();
            fetchUpstreamConfig();

            // Refresh every 30 seconds
            setInterval(fetchConfigurations, 30000);

            // Close modals on outside click
            document.getElementById('edit-modal').addEventListener('click', (e) => {
                if (e.target.id === 'edit-modal') {
                    closeEditModal();
                }
            });

            document.getElementById('add-modal').addEventListener('click', (e) => {
                if (e.target.id === 'add-modal') {
                    closeAddModal();
                }
            });
        </script>
    </body>
    </html>
    """

    return Response(content=html_content, media_type="text/html")
