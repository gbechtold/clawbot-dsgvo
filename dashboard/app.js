const API_BASE = '/api/v1';
const DEFAULT_TENANT = 'default';
const REFRESH_INTERVAL = 10000; // 10 seconds

let refreshTimer;

// Format timestamp
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('de-AT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Fetch signals
async function fetchSignals() {
    try {
        const response = await fetch(`${API_BASE}/signals?tenant_id=${DEFAULT_TENANT}&limit=20`);
        if (!response.ok) throw new Error('Failed to fetch signals');
        return await response.json();
    } catch (error) {
        console.error('Error fetching signals:', error);
        return null;
    }
}

// Fetch audit log
async function fetchAuditLog() {
    try {
        const response = await fetch(`${API_BASE}/audit-log?tenant_id=${DEFAULT_TENANT}&limit=10`);
        if (!response.ok) throw new Error('Failed to fetch audit log');
        return await response.json();
    } catch (error) {
        console.error('Error fetching audit log:', error);
        return null;
    }
}

// Fetch compliance report
async function fetchComplianceReport() {
    try {
        const response = await fetch(`${API_BASE}/compliance/report?tenant_id=${DEFAULT_TENANT}`);
        if (!response.ok) throw new Error('Failed to fetch compliance report');
        return await response.json();
    } catch (error) {
        console.error('Error fetching compliance report:', error);
        return null;
    }
}

// Render signals
function renderSignals(data) {
    const container = document.getElementById('signals-container');

    if (!data || !data.signals || data.signals.length === 0) {
        container.innerHTML = '<div class="loading">No signals found</div>';
        return;
    }

    container.innerHTML = data.signals.map(signal => `
        <div class="signal-card">
            <div class="signal-header">
                <div class="signal-id">${signal.signal_id}</div>
            </div>
            <div class="signal-badges">
                <span class="badge urgency-${signal.urgency}">${signal.urgency}</span>
                <span class="badge sentiment-${signal.sentiment}">${signal.sentiment}</span>
                <span class="badge category">${signal.category}</span>
            </div>
            <div class="signal-content">
                ${signal.anonymized_content}
            </div>
            <div class="signal-meta">
                ${formatTimestamp(signal.created_at)}
            </div>
        </div>
    `).join('');
}

// Render audit log
function renderAuditLog(data) {
    const container = document.getElementById('audit-container');

    if (!data || !data.entries || data.entries.length === 0) {
        container.innerHTML = '<div class="loading">No audit entries found</div>';
        return;
    }

    container.innerHTML = data.entries.map(entry => `
        <div class="audit-entry">
            <div>
                <span class="audit-action">${entry.action}</span>
                <span class="audit-details">
                    ${entry.signal_id ? `Signal: ${entry.signal_id}` : ''}
                    ${entry.actor ? `• Actor: ${entry.actor}` : ''}
                </span>
            </div>
            <div class="audit-time">${formatTimestamp(entry.timestamp)}</div>
        </div>
    `).join('');
}

// Update stats
function updateStats(complianceData) {
    if (!complianceData) return;

    document.getElementById('total-signals').textContent = complianceData.total_signals;
    document.getElementById('pii-anonymized').textContent = complianceData.pii_anonymized;
    document.getElementById('audit-entries').textContent = complianceData.audit_entries;

    // Count critical urgency from details
    const criticalCount = complianceData.details?.urgency_levels?.critical || 0;
    document.getElementById('critical-urgency').textContent = criticalCount;
}

// Refresh dashboard
async function refreshDashboard() {
    console.log('Refreshing dashboard...');

    const [signalsData, auditData, complianceData] = await Promise.all([
        fetchSignals(),
        fetchAuditLog(),
        fetchComplianceReport()
    ]);

    renderSignals(signalsData);
    renderAuditLog(auditData);
    updateStats(complianceData);

    document.getElementById('last-update').textContent = new Date().toLocaleTimeString('de-AT');
}

// Start auto-refresh
function startAutoRefresh() {
    stopAutoRefresh();
    refreshTimer = setInterval(refreshDashboard, REFRESH_INTERVAL);
}

// Stop auto-refresh
function stopAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
    }
}

// Initialize dashboard
async function init() {
    console.log('Initializing ClawBot Dashboard...');

    // Initial load
    await refreshDashboard();

    // Start auto-refresh
    startAutoRefresh();

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', async () => {
        await refreshDashboard();
        startAutoRefresh(); // Reset timer
    });

    // Stop refresh when page is hidden
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            stopAutoRefresh();
        } else {
            startAutoRefresh();
        }
    });
}

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
