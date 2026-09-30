/**
 * Olist Marketing Funnel & Revenue Analytics Web Dashboard Application
 * Handles API data fetching, Plotly rendering, interactive simulation, and UI state.
 */

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

// Global state variables
let globalFunnelData = [];
let globalLeadExplorerData = [];
let globalRoiData = [];
let globalSegmentData = [];
let simBudgetChanges = {};

async function initApp() {
    setupThemeToggle();
    await fetchOverviewData();
    await fetchChannelRoiData();
    await fetchRecommendations();
    await fetchAnomalies();
    await fetchFunnelData();
    await fetchSpeedData();
    await fetchRevenueData();
    await fetchSegmentData();
    await fetchAuditData();
    await fetchExplorerData();
    initSimulator();
}

// ------------------------------------------------------------------------------
// 1. THEME SWITCHER (WITH Plotly TEXT CONTRAST FIX)
// ------------------------------------------------------------------------------
function setupThemeToggle() {
    const btn = document.getElementById('theme-toggle');
    const label = document.getElementById('theme-label');

    btn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        label.innerText = newTheme === 'dark' ? 'Dark' : 'Light';
        btn.querySelector('i').className = newTheme === 'dark' ? 'fa-solid fa-moon' : 'fa-solid fa-sun';

        // Re-render all Plotly charts for crystal-clear text contrast
        if (globalRoiData.length > 0) renderExecutiveROIChart(globalRoiData);
        if (globalFunnelData.length > 0) renderFunnelChart(globalFunnelData);
        if (globalSegmentData.length > 0) renderSegmentDistChart(globalSegmentData);
    });
}

// Helper: Get theme text & grid colors
function getThemeColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
        isDark: isDark,
        textColor: isDark ? '#f8fafc' : '#0f172a',
        subtextColor: isDark ? '#94a3b8' : '#334155',
        gridColor: isDark ? '#1e293b' : '#cbd5e1'
    };
}

// ------------------------------------------------------------------------------
// 2. OVERVIEW KPI CARDS & EXECUTIVE ROI BAR
// ------------------------------------------------------------------------------
async function fetchOverviewData() {
    try {
        const res = await fetch('/api/overview');
        const data = await res.json();

        document.getElementById('kpi-mqls').innerText = data.total_mqls.toLocaleString();
        document.getElementById('kpi-closed').innerText = data.total_closed_deals.toLocaleString();
        document.getElementById('kpi-conv').innerText = (data.overall_conversion_rate * 100).toFixed(2) + '%';
        document.getElementById('kpi-rev').innerText = '$' + data.total_post_signing_revenue.toLocaleString(undefined, {minimumFractionDigits: 2});
        document.getElementById('kpi-rev-deal').innerText = '$' + data.revenue_per_closed_deal.toLocaleString(undefined, {minimumFractionDigits: 2});
    } catch (err) {
        console.error('Error fetching overview data:', err);
    }
}

async function fetchChannelRoiData() {
    try {
        const res = await fetch('/api/roi');
        globalRoiData = await res.json();
        renderExecutiveROIChart(globalRoiData);
    } catch (err) {
        console.error('Error fetching channel ROI data:', err);
    }
}

function renderExecutiveROIChart(roiData) {
    const theme = getThemeColors();
    const origins = roiData.map(d => formatOrigin(d.origin));
    const roiMultiples = roiData.map(d => d.roi_multiple);
    const profits = roiData.map(d => d.net_profit);

    const trace = {
        y: origins,
        x: roiMultiples,
        type: 'bar',
        orientation: 'h',
        text: roiMultiples.map(v => `${v}x ROI`),
        textposition: 'inside',
        marker: {
            color: roiMultiples.map(v => v >= 15 ? '#059669' : v >= 8 ? '#3b82f6' : v >= 4 ? '#f59e0b' : '#ef4444'),
            opacity: 0.88
        }
    };

    const layout = {
        margin: { l: 140, r: 40, t: 20, b: 50 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: {
            title: 'Channel ROI Multiple (Post-Signing Revenue / CAC Spend)',
            color: theme.subtextColor,
            gridcolor: theme.gridColor
        },
        yaxis: {
            autorange: 'reversed',
            color: theme.textColor
        },
        font: { family: 'Inter, sans-serif', color: theme.textColor }
    };

    Plotly.newPlot('chart-executive-roi', [trace], layout, {responsive: true});
}

// ------------------------------------------------------------------------------
// 3. RECOMMENDATIONS & ANOMALIES (CLEVER FEATURES #1 & #2)
// ------------------------------------------------------------------------------
async function fetchRecommendations() {
    try {
        const res = await fetch('/api/recommendations');
        const recs = await res.json();
        const container = document.getElementById('recommendations-container');
        container.innerHTML = '';

        recs.forEach(r => {
            const item = document.createElement('div');
            item.className = 'rec-item';
            item.innerHTML = `
                <div class="item-top">
                    <span class="item-title">${formatOrigin(r.origin)}</span>
                    <span class="badge badge-${r.badge_color}">${r.strategy}</span>
                </div>
                <div class="item-body">
                    <p style="margin-bottom: 0.3rem;"><strong>Action:</strong> ${r.recommended_action}</p>
                    <p style="font-size: 0.8rem; opacity: 0.9;"><em>Rationale:</em> ${r.strategic_rationale}</p>
                </div>
            `;
            container.appendChild(item);
        });
    } catch (err) {
        console.error('Error fetching recommendations:', err);
    }
}

async function fetchAnomalies() {
    try {
        const res = await fetch('/api/anomalies');
        const anomalies = await res.json();
        const container = document.getElementById('anomalies-container');
        container.innerHTML = '';

        if (anomalies.length === 0) {
            container.innerHTML = '<p class="subtitle text-success"><i class="fa-solid fa-check"></i> No critical anomalies detected in acquisition pipeline.</p>';
            return;
        }

        anomalies.forEach(a => {
            const item = document.createElement('div');
            item.className = 'anomaly-item';
            item.innerHTML = `
                <div class="item-top">
                    <span class="item-title text-danger"><i class="fa-solid fa-triangle-exclamation"></i> ${a.type}</span>
                    <span class="badge badge-danger">${a.severity}</span>
                </div>
                <div class="item-body">
                    <p><strong>Channel:</strong> ${formatOrigin(a.origin)} | <strong>Metrics:</strong> ${a.metric}</p>
                    <p style="margin-top: 0.2rem;">${a.insight}</p>
                    <p style="font-size: 0.8rem; color: var(--color-amber); margin-top: 0.3rem;"><strong>Recommendation:</strong> ${a.recommendation}</p>
                </div>
            `;
            container.appendChild(item);
        });
    } catch (err) {
        console.error('Error fetching anomalies:', err);
    }
}

// ------------------------------------------------------------------------------
// 4. FUNNEL CONVERSION CHART & TABLE
// ------------------------------------------------------------------------------
async function fetchFunnelData() {
    try {
        const res = await fetch('/api/funnel');
        const payload = await res.json();
        globalFunnelData = payload.funnel_data;

        // Update Chi-Square Badge
        const chi = payload.chi_square_test;
        document.getElementById('chi-square-badge').innerHTML = 
            `Chi-Square Stat: <strong>${chi.chi2_stat}</strong> | p-value: <strong class="text-success">${chi.p_value.toExponential(2)}</strong> (Significant)`;

        renderFunnelChart(globalFunnelData);
        populateFunnelTable(globalFunnelData);
    } catch (err) {
        console.error('Error fetching funnel data:', err);
    }
}

function renderFunnelChart(data) {
    const theme = getThemeColors();
    const origins = data.map(d => formatOrigin(d.origin));
    const rates = data.map(d => d.conversion_rate * 100);
    const errLow = data.map(d => (d.conversion_rate - d.wilson_ci_lower) * 100);
    const errHigh = data.map(d => (d.wilson_ci_upper - d.conversion_rate) * 100);

    const trace = {
        y: origins,
        x: rates,
        type: 'bar',
        orientation: 'h',
        marker: { color: '#3b82f6', opacity: 0.88 },
        error_x: {
            type: 'data',
            symmetric: false,
            array: errHigh,
            arrayminus: errLow,
            color: '#1e3a8a',
            thickness: 2,
            width: 5
        }
    };

    const layout = {
        margin: { l: 140, r: 40, t: 20, b: 50 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: {
            title: 'Conversion Rate (%) [95% Wilson CIs]',
            color: theme.subtextColor,
            gridcolor: theme.gridColor
        },
        yaxis: {
            autorange: 'reversed',
            color: theme.textColor
        },
        font: { family: 'Inter, sans-serif', color: theme.textColor }
    };

    Plotly.newPlot('chart-funnel-ci', [trace], layout, {responsive: true});
}

function populateFunnelTable(data) {
    const tbody = document.querySelector('#table-funnel tbody');
    tbody.innerHTML = '';
    data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${formatOrigin(row.origin)}</strong></td>
            <td>${row.mqls.toLocaleString()}</td>
            <td>${row.closed_deals.toLocaleString()}</td>
            <td><strong class="text-blue">${(row.conversion_rate * 100).toFixed(2)}%</strong></td>
            <td>${(row.wilson_ci_lower * 100).toFixed(2)}%</td>
            <td>${(row.wilson_ci_upper * 100).toFixed(2)}%</td>
        `;
        tbody.appendChild(tr);
    });
}

// ------------------------------------------------------------------------------
// 5. SPEED & KAPLAN-MEIER SURVIVAL CHART
// ------------------------------------------------------------------------------
async function fetchSpeedData() {
    try {
        const res = await fetch('/api/speed');
        const data = await res.json();
        renderSurvivalChart(data.survival_curves);
    } catch (err) {
        console.error('Error fetching speed data:', err);
    }
}

function renderSurvivalChart(curves) {
    const theme = getThemeColors();
    const traces = [];
    const colors = ['#1e40af', '#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#db2777'];
    let idx = 0;

    for (const [orig, curve] of Object.entries(curves)) {
        if (idx >= 6) break;
        traces.push({
            x: curve.times,
            y: curve.probabilities,
            mode: 'lines',
            line: { shape: 'hv', color: colors[idx % colors.length], width: 2.5 },
            name: formatOrigin(orig)
        });
        idx++;
    }

    const layout = {
        margin: { l: 50, r: 30, t: 20, b: 50 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: { title: 'Days Since First Contact', color: theme.subtextColor, gridcolor: theme.gridColor },
        yaxis: { title: 'Probability of Remaining Unwon (Survival S(t))', color: theme.subtextColor, gridcolor: theme.gridColor },
        legend: { font: { color: theme.textColor } },
        font: { family: 'Inter, sans-serif', color: theme.textColor }
    };

    Plotly.newPlot('chart-survival', traces, layout, {responsive: true});
}

// ------------------------------------------------------------------------------
// 6. REVENUE DEPTH, BOOTSTRAP CIs & SEGMENTS
// ------------------------------------------------------------------------------
async function fetchRevenueData() {
    try {
        const res = await fetch('/api/revenue');
        const data = await res.json();
        renderBootstrapRevChart(data.bootstrap_cis);
        renderSensitivityChart(data.sensitivity_windows, '365d');
    } catch (err) {
        console.error('Error fetching revenue data:', err);
    }
}

async function fetchSegmentData() {
    try {
        const res = await fetch('/api/segments');
        globalSegmentData = await res.json();
        renderSegmentDistChart(globalSegmentData);
    } catch (err) {
        console.error('Error fetching segment data:', err);
    }
}

function renderBootstrapRevChart(bootData) {
    const theme = getThemeColors();
    const origins = bootData.map(d => formatOrigin(d.origin));
    const means = bootData.map(d => d.mean_revenue_per_deal);
    const errLow = bootData.map(d => d.mean_revenue_per_deal - d.boot_ci_lower);
    const errHigh = bootData.map(d => d.boot_ci_upper - d.mean_revenue_per_deal);

    const trace = {
        y: origins,
        x: means,
        type: 'bar',
        orientation: 'h',
        marker: { color: '#059669', opacity: 0.88 },
        error_x: { type: 'data', symmetric: false, array: errHigh, arrayminus: errLow, color: '#065f46', thickness: 2 }
    };

    const layout = {
        margin: { l: 140, r: 40, t: 20, b: 50 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: { title: 'Revenue Post-Signing per Deal ($) [95% Bootstrap CIs]', color: theme.subtextColor, gridcolor: theme.gridColor },
        yaxis: { autorange: 'reversed', color: theme.textColor },
        font: { family: 'Inter, sans-serif', color: theme.textColor }
    };

    Plotly.newPlot('chart-bootstrap-rev', [trace], layout, {responsive: true});
}

function renderSensitivityChart(sensData, windowKey) {
    const theme = getThemeColors();
    const origins = sensData.map(d => formatOrigin(d.origin));
    const vals = sensData.map(d => d['rev_per_deal_' + windowKey]);

    const trace = {
        x: origins,
        y: vals,
        type: 'bar',
        marker: { color: '#7c3aed', opacity: 0.88 }
    };

    const layout = {
        margin: { l: 50, r: 20, t: 20, b: 80 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: { color: theme.textColor, tickangle: -30 },
        yaxis: { title: `Revenue per Deal ($) [Window: ${windowKey}]`, color: theme.subtextColor, gridcolor: theme.gridColor },
        font: { family: 'Inter, sans-serif', color: theme.textColor }
    };

    Plotly.newPlot('chart-sensitivity', [trace], layout, {responsive: true});
}

function renderSegmentDistChart(segmentData) {
    const theme = getThemeColors();
    const segments = segmentData.map(d => formatOrigin(d.segment_name));
    const revenues = segmentData.map(d => d.total_revenue);

    const trace = {
        x: segments,
        y: revenues,
        type: 'bar',
        marker: { color: '#d97706', opacity: 0.88 }
    };

    const layout = {
        margin: { l: 60, r: 20, t: 20, b: 90 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: { color: theme.textColor, tickangle: -35 },
        yaxis: { title: 'Total Post-Signing Revenue ($)', color: theme.subtextColor, gridcolor: theme.gridColor },
        font: { family: 'Inter, sans-serif', color: theme.textColor }
    };

    Plotly.newPlot('chart-segments-dist', [trace], layout, {responsive: true});
}

function switchSensitivity(key) {
    document.querySelectorAll('.toggle-group .btn-toggle').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    fetch('/api/revenue').then(r => r.json()).then(d => renderSensitivityChart(d.sensitivity_windows, key));
}

// ------------------------------------------------------------------------------
// 7. DATA AUDIT DASHBOARD TAB
// ------------------------------------------------------------------------------
async function fetchAuditData() {
    try {
        const res = await fetch('/api/audit');
        const audit = await res.json();

        document.getElementById('audit-mqls').innerText = audit.total_mqls.toLocaleString();
        document.getElementById('audit-deals').innerText = audit.total_closed_deals.toLocaleString();
        document.getElementById('audit-null-origin').innerText = audit.mql_null_origins.toLocaleString();
        document.getElementById('audit-activation').innerText = audit.activation_rate_pct.toFixed(1) + '%';
    } catch (err) {
        console.error('Error fetching audit data:', err);
    }
}

// ------------------------------------------------------------------------------
// 8. WHAT-IF BUDGET ALLOCATOR SIMULATOR (CLEVER FEATURE #3)
// ------------------------------------------------------------------------------
function initSimulator() {
    const container = document.getElementById('simulator-sliders-container');
    container.innerHTML = '';

    const channels = ['paid_search', 'referral', 'organic_search', 'email', 'direct_traffic', 'social', 'organic_social', 'display'];

    channels.forEach(ch => {
        simBudgetChanges[ch] = 0;
        const group = document.createElement('div');
        group.className = 'sim-slider-group';
        group.innerHTML = `
            <div class="sim-slider-header">
                <span>${formatOrigin(ch)}</span>
                <span id="slider-val-${ch}" class="text-blue">+0%</span>
            </div>
            <input type="range" class="sim-slider-input" min="-50" max="50" value="0" step="5" oninput="updateSliderVal('${ch}', this.value)">
        `;
        container.appendChild(group);
    });
}

function updateSliderVal(ch, val) {
    const num = parseInt(val);
    simBudgetChanges[ch] = num;
    const label = document.getElementById(`slider-val-${ch}`);
    label.innerText = (num >= 0 ? '+' : '') + num + '%';
    label.className = num > 0 ? 'text-success' : num < 0 ? 'text-danger' : 'text-blue';
}

async function runSimulation() {
    try {
        const res = await fetch('/api/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ budget_changes: simBudgetChanges })
        });
        const sim = await res.json();

        document.getElementById('sim-base-rev').innerText = '$' + sim.total_baseline_revenue.toLocaleString(undefined, {minimumFractionDigits: 2});
        document.getElementById('sim-proj-rev').innerText = '$' + sim.total_simulated_revenue.toLocaleString(undefined, {minimumFractionDigits: 2});
        
        const delta = sim.net_revenue_delta;
        const deltaEl = document.getElementById('sim-delta');
        deltaEl.innerText = (delta >= 0 ? '+$' : '-$') + Math.abs(delta).toLocaleString(undefined, {minimumFractionDigits: 2});
        deltaEl.className = delta >= 0 ? 'sim-value text-emerald' : 'sim-value text-danger';

        const liftEl = document.getElementById('sim-roi-lift');
        liftEl.innerText = (sim.roi_lift_pct >= 0 ? '+' : '') + sim.roi_lift_pct.toFixed(2) + '%';
        liftEl.className = sim.roi_lift_pct >= 0 ? 'sim-value text-warning' : 'sim-value text-danger';

    } catch (err) {
        console.error('Error running simulation:', err);
    }
}

// ------------------------------------------------------------------------------
// 9. DATA EXPLORER & CSV EXPORTER
// ------------------------------------------------------------------------------
async function fetchExplorerData() {
    try {
        const res = await fetch('/api/data/leads?limit=100');
        globalLeadExplorerData = await res.json();
        renderExplorerTable(globalLeadExplorerData);
    } catch (err) {
        console.error('Error fetching explorer data:', err);
    }
}

function renderExplorerTable(data) {
    const tbody = document.querySelector('#table-explorer tbody');
    tbody.innerHTML = '';
    data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>#${row.lead_key}</td>
            <td><code>${row.mql_id.substring(0, 12)}...</code></td>
            <td>${formatOrigin(row.origin_name)}</td>
            <td><code>${row.landing_page_id.substring(0, 10)}...</code></td>
            <td>${row.is_won ? '<span class="badge badge-success">Won</span>' : '<span class="badge badge-danger">Unwon</span>'}</td>
            <td>${row.days_to_close !== null ? row.days_to_close + ' days' : '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}

function filterExplorerTable() {
    const query = document.getElementById('table-search').value.toLowerCase();
    const filtered = globalLeadExplorerData.filter(d => 
        d.mql_id.toLowerCase().includes(query) || d.origin_name.toLowerCase().includes(query)
    );
    renderExplorerTable(filtered);
}

function exportDataCSV() {
    window.location.href = '/api/data/leads?limit=10000';
}

// Helper: Format channel origin strings
function formatOrigin(str) {
    if (!str) return 'Unknown';
    return str.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// Tab switcher
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    const activeBtn = document.getElementById('tab-btn-' + tabId);
    if (activeBtn) activeBtn.classList.add('active');
    
    const activeContent = document.getElementById('tab-' + tabId);
    if (activeContent) activeContent.classList.add('active');

    // Trigger Plotly resize for charts inside newly activated tab
    window.dispatchEvent(new Event('resize'));
}
