/**
 * Dashboard page logic — loads stats and analytics.
 */

let revenueChart = null;
let statusChart = null;
let map = null;
let lastAnalyticsData = null; // Global store for fullscreen
let fsMap = null; // Map instance for fullscreen

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    setNavUsername();
    initCharts();
    initMap();
    loadDashboard();
    setupAdminControls();
});

async function setupAdminControls() {
    const user = JSON.parse(sessionStorage.getItem('user_data') || '{}');
    if (user.role === 'admin') {
        const controls = document.getElementById('adminControls');
        if (!controls) return;
        controls.style.display = 'flex';
        
        const selector = document.getElementById('userSelector');
        try {
            const orgUsers = await ApiClient.request('/org/users');
            orgUsers.forEach(u => {
                if (u.role !== 'admin') {
                    const opt = document.createElement('option');
                    opt.value = u.id;
                    opt.textContent = `${u.email.split('@')[0]} (${u.email})`;
                    selector.appendChild(opt);
                }
            });
            
            selector.addEventListener('change', () => {
                const selectedText = selector.options[selector.selectedIndex].text;
                loadDashboard(selector.value, selectedText);
            });
        } catch (e) {
            console.error("Failed to load org users:", e);
        }
    }
}

function initCharts() {
    const ctxRevenue = document.getElementById('revenueChart').getContext('2d');
    const ctxStatus = document.getElementById('statusChart').getContext('2d');
    
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                labels: { color: '#888', font: { family: 'Inter' } }
            }
        },
        scales: {
            y: { ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,0.05)' } },
            x: { ticks: { color: '#888' }, grid: { display: false } }
        }
    };

    revenueChart = new Chart(ctxRevenue, {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Revenue (Paid)', data: [], borderColor: '#FF5722', backgroundColor: 'rgba(255, 87, 34, 0.1)', fill: true, tension: 0.4 }] },
        options: chartOptions
    });

    statusChart = new Chart(ctxStatus, {
        type: 'doughnut',
        data: { labels: [], datasets: [{ data: [], backgroundColor: ['#FF5722', '#4CAF50', '#2196F3', '#FFC107', '#9E9E9E'] }] },
        options: { ...chartOptions, scales: {} }
    });
}

function initMap() {
    map = L.map('heatmap').setView([20.5937, 78.9629], 5);
    // Switch to Google Maps Roadmap representation
    L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
        attribution: 'Map data &copy; Google'
    }).addTo(map);
}

async function loadDashboard(userId = null, userDisplayName = null) {
    const user = JSON.parse(sessionStorage.getItem('user_data') || '{}');
    const titleEl = document.getElementById('dashboardTitle');
    
    // Update Title based on selection
    if (userId) {
        titleEl.innerHTML = `Dashboard <span style="color: var(--accent-orange); font-size: 0.6em; margin-left: 10px; opacity: 0.8;">[${userDisplayName}]</span>`;
    } else {
        titleEl.innerHTML = `Dashboard <span style="color: var(--text-secondary); font-size: 0.6em; margin-left: 10px; opacity: 0.5;">[GLOBAL]</span>`;
    }
    
    try {
        const data = await ApiClient.getDashboardStats(userId);
        lastAnalyticsData = data; // Cache for fullscreen
        console.log("DEBUG: Dashboard Data Received:", data);
        
        // Update Stats Row
        updateStats(data.stats || []);
        
        // Update Charts
        updateRevenueChart(data.monthly_revenue || []);
        updateStatusChart(data.stats || []);
        
        // Update Heatmap
        if (data.heatmap && data.heatmap.length > 0) {
            updateHeatmap(data.heatmap);
        } else {
            if (window._mapMarkers) window._mapMarkers.forEach(m => map.removeLayer(m));
        }

        // Update Recent Invoices (FILTERED BY USER ID)
        const invoices = await ApiClient.getInvoices(0, 10, '', '', userId);
        renderRecentInvoices(invoices.filter(i => !i.is_template), user.role === 'admin');
        
        // Render Templates
        renderTemplates(invoices.filter(i => i.is_template));

    } catch (e) {
        console.error("Dashboard error:", e);
    }
}

function renderTemplates(templates) {
    const container = document.getElementById('templatesGrid');
    
    // Always include a system default template
    const defaultTemplate = {
        _id: 'system_default',
        client_name: 'Standard Professional',
        recurrence: 'System',
        invoice_number_prefix: 'DEF-',
        grand_total: 0,
        currency: 'INR',
        is_system: true
    };

    const displayTemplates = [defaultTemplate, ...(templates || [])];

    container.innerHTML = displayTemplates.map(t => `
        <div class="glass-panel stat-card hover-specular" style="display: flex; flex-direction: column; justify-content: space-between; padding: 20px; ${t.is_system ? 'border-color: var(--accent-orange) !important;' : ''}">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="font-weight: 700; font-size: 14px;">${t.client_name} ${t.is_system ? '<i class="fas fa-star" style="color:var(--accent-orange); font-size:0.8em; margin-left:5px;"></i>' : ''}</div>
                    <span class="badge ${t.is_system ? 'badge-sent' : 'badge-paid'}" style="font-size: 9px; padding: 2px 6px;">${t.recurrence.toUpperCase()}</span>
                </div>
                <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">${t.is_system ? 'Permanent System Layout' : (t.invoice_number_prefix || 'INV-') + ' [Template]'}</div>
                <div style="font-size: 16px; font-weight: 800; color: var(--accent-orange); margin-top: 12px;">${t.is_system ? 'READY TO USE' : formatCurrency(t.grand_total, t.currency)}</div>
            </div>
            <button onclick="cloneInvoice('${t._id}', ${t.is_system})" class="btn btn-secondary" style="width: 100%; margin-top: 20px; font-size: 11px; padding: 8px;">
                ${t.is_system ? 'USE TEMPLATE' : 'CLONE DRAFT'}
            </button>
        </div>
    `).join('');
}

async function cloneInvoice(id, isSystem = false) {
    if (isSystem) {
        window.location.href = '/create';
        return;
    }
    if (!confirm('Clone this template into a new draft?')) return;
    
    try {
        showToast('Creating draft...', 'info');
        const newInv = await ApiClient.cloneInvoice(id);
        showToast('Draft created! Redirecting...', 'success');
        setTimeout(() => window.location.href = `/invoices`, 1000);
    } catch (e) {
        console.error(e);
    }
}

function updateStats(stats) {
    let totalInvoices = 0;
    let revenue = 0;
    let pending = 0;

    stats.forEach(s => {
        totalInvoices += s.count;
        if (s._id.is_paid) revenue += s.total_amount;
        // Pending is Sent but not Paid
        if (s._id.is_sent && !s._id.is_paid) pending += s.total_amount;
    });

    document.getElementById('statTotal').textContent = totalInvoices;
    document.getElementById('statRevenue').textContent = formatCurrency(revenue);
    document.getElementById('statPending').textContent = formatCurrency(pending);
}

function updateRevenueChart(data) {
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    revenueChart.data.labels = data.map(d => `${months[d._id.month - 1]} ${d._id.year}`);
    revenueChart.data.datasets[0].data = data.map(d => d.revenue);
    revenueChart.update();
}

function updateStatusChart(stats) {
    const labels = [];
    const counts = [];
    const colors = [];

    stats.forEach(s => {
        const { is_sent, is_paid } = s._id;
        let label = "DRAFT";
        let color = "#888888"; // Grey

        if (!is_sent && !is_paid) {
            label = "DRAFT (NOT SENT)";
            color = "#888888";
        } else if (is_sent && !is_paid) {
            label = "AWAITING PAYMENT (SENT)";
            color = "#FF9800"; // Orange
        } else if (!is_sent && is_paid) {
            label = "PRE-PAID (UNSENT)";
            color = "#FFC107"; // Amber/Gold (Paid status)
        } else if (is_sent && is_paid) {
            label = "COMPLETED";
            color = "#4CAF50"; // Green
        }

        labels.push(label);
        counts.push(s.count);
        colors.push(color);
    });

    statusChart.data.labels = labels;
    statusChart.data.datasets[0].data = counts;
    statusChart.data.datasets[0].backgroundColor = colors;
    statusChart.update();
}

function updateHeatmap(points) {
    // Clear existing map layers (markers)
    if (window._mapMarkers) {
        window._mapMarkers.forEach(m => map.removeLayer(m));
    }
    window._mapMarkers = [];
    
    if (points.length === 0) return;

    const cityMap = {};
    points.forEach(p => {
        const key = p.city || `${p.lat.toFixed(4)},${p.lng.toFixed(4)}`;
        if (!cityMap[key]) {
            cityMap[key] = { lat: p.lat, lng: p.lng, count: 0, revenue: 0, name: p.city || "Unknown Location" };
        }
        cityMap[key].count += 1;
        cityMap[key].revenue += p.weight;
    });

    const aggregated = Object.values(cityMap);
    const maxCount = Math.max(...aggregated.map(a => a.count));

    aggregated.forEach(city => {
        // More conservative scaling: Base 5px, Max 12px
        // We use Math.sqrt or log scaling so it doesn't grow linearly
        const scaleFactor = maxCount > 1 ? (Math.log(city.count + 1) / Math.log(maxCount + 1)) : 0;
        const radius = 5 + (scaleFactor * 7); // Range: 5px to 12px
        
        // Color based on count
        let color = '#FF5722'; // Default Orange
        if (city.count > 10) color = '#FF5722'; // High (Orange)
        else if (city.count > 5) color = '#FFC107'; // Orange (Medium)
        else if (city.count > 2) color = '#4CAF50'; // Green (Low)

        const marker = L.circleMarker([city.lat, city.lng], {
            radius: radius,
            fillColor: color,
            color: '#fff',
            weight: 1,
            opacity: 0.8,
            fillOpacity: 0.6
        }).addTo(map);

        // Hover tooltip
        marker.bindTooltip(`
            <div style="font-family: 'Inter', sans-serif; padding: 4px;">
                <b style="color: ${color}">${city.name}</b><br/>
                Total Invoices: <b>${city.count}</b><br/>
                Total Revenue: <b>₹ ${city.revenue.toLocaleString()}</b>
            </div>
        `, { sticky: true, className: 'glass-tooltip' });

        window._mapMarkers.push(marker);
    });
    
    const bounds = L.latLngBounds(aggregated.map(p => [p.lat, p.lng]));
    map.fitBounds(bounds, { padding: [50, 50] });
}

function renderRecentInvoices(invoices, isAdmin = false) {
    const container = document.getElementById('recentInvoices');
    if (!invoices || invoices.length === 0) {
        container.innerHTML = `<div class="glass-panel" style="padding: 20px; text-align: center; color: var(--text-secondary);">No recent activity.</div>`;
        return;
    }

    container.innerHTML = invoices.map(inv => `
        <a href="/invoices?id=${inv._id}" class="invoice-row glass-panel hover-specular" style="margin-bottom: 8px; grid-template-columns: ${isAdmin ? '1fr 2fr 1fr 1.5fr 1.5fr 1fr' : '1fr 2fr 1fr 1.5fr 1fr'};">
            <div class="invoice-number">${inv.invoice_number}</div>
            <div class="invoice-client">${inv.client_name}</div>
            <div class="invoice-date">${formatDate(inv.date)}</div>
            <div class="invoice-amount">${formatCurrency(inv.grand_total, inv.currency)}</div>
            ${isAdmin ? `<div style="font-size: 11px; color: var(--accent-orange);">${inv.created_by.split('@')[0]}</div>` : ''}
            <div><span class="badge badge-${inv.status}">${inv.status}</span></div>
        </a>
    `).join('');
}
// Fullscreen Analysis Logic
function openFullscreen(type) {
    const modal = document.getElementById('fsModal');
    const chartCont = document.getElementById('fsChartContainer');
    const mapCont = document.getElementById('fsMapContainer');
    const detailsList = document.getElementById('fsDetailsList');
    const title = document.getElementById('fsTitle');
    
    modal.classList.add('active');
    chartCont.style.display = 'none';
    mapCont.style.display = 'none';
    detailsList.innerHTML = '';

    if (!lastAnalyticsData) return;

    if (type === 'chart') {
        title.innerText = 'Status Distribution Analysis';
        chartCont.style.display = 'block';
        renderFullscreenChart(lastAnalyticsData.stats);
    } else if (type === 'map') {
        title.innerText = 'Geospatial Business Reach';
        mapCont.style.display = 'block';
        renderFullscreenMap(lastAnalyticsData.heatmap);
    }
}

function closeFullscreen() {
    document.getElementById('fsModal').classList.remove('active');
}

function renderFullscreenChart(stats) {
    const ctx = document.getElementById('statusChartLarge').getContext('2d');
    if (window._fsChart) window._fsChart.destroy();
    
    const labels = stats.map(s => s._id.toUpperCase());
    const dataPoints = stats.map(s => s.count);
    
    window._fsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: dataPoints,
                backgroundColor: ['#FF5722', '#4CAF50', '#2196F3', '#FFC107', '#9E9E9E'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#888', font: { size: 14 } } }
            }
        }
    });

    // Render Side Details
    const list = document.getElementById('fsDetailsList');
    const totalCount = dataPoints.reduce((a, b) => a + b, 0);
    const totalRev = stats.reduce((a, b) => a + b.total_amount, 0);

    list.innerHTML = `
        <div class="detail-row"><span class="detail-label">Total Volume</span><span class="detail-value">${totalCount} Invoices</span></div>
        <div class="detail-row" style="margin-bottom: 20px;"><span class="detail-label">Total Value</span><span class="detail-value">${formatCurrency(totalRev)}</span></div>
        <h5 style="font-size: 10px; color: var(--text-secondary); margin-bottom: 10px;">BREAKDOWN</h5>
    `;

    stats.forEach(s => {
        const pct = ((s.count / totalCount) * 100).toFixed(1);
        list.innerHTML += `
            <div class="detail-row">
                <span class="detail-label">${s._id.toUpperCase()}</span>
                <span class="detail-value">${formatCurrency(s.total_amount)} (${pct}%)</span>
            </div>
        `;
    });
}

function renderFullscreenMap(points) {
    // Small delay to ensure container is visible before Leaflet inits
    setTimeout(() => {
        if (fsMap) fsMap.remove();
        fsMap = L.map('fsMapContainer', { zoomControl: false }).setView([20.5937, 78.9629], 5);
        L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
            maxZoom: 20,
            subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
            attribution: 'Map data &copy; Google'
        }).addTo(fsMap);

        const cityMap = {};
        points.forEach(p => {
            const key = p.city || `${p.lat.toFixed(2)},${p.lng.toFixed(2)}`;
            if (!cityMap[key]) cityMap[key] = { lat: p.lat, lng: p.lng, count: 0, revenue: 0, name: p.city || "Unknown" };
            cityMap[key].count++;
            cityMap[key].revenue += p.weight;
        });

        const aggregated = Object.values(cityMap);
        aggregated.forEach(city => {
            L.circleMarker([city.lat, city.lng], {
                radius: 6 + (Math.min(city.count / 5, 1) * 10),
                fillColor: city.count > 5 ? '#FF5722' : '#2196F3',
                color: '#fff',
                weight: 1,
                fillOpacity: 0.7
            }).addTo(fsMap).bindTooltip(`<b>${city.name}</b><br>Count: ${city.count}<br>Revenue: ₹${city.revenue.toLocaleString()}`);
        });
        
        const bounds = L.latLngBounds(aggregated.map(p => [p.lat, p.lng]));
        if (bounds.isValid()) fsMap.fitBounds(bounds, { padding: [100, 100] });

        // Sidebar Details for Map
        const list = document.getElementById('fsDetailsList');
        const sortedHubs = Object.values(cityMap).sort((a, b) => b.revenue - a.revenue);
        const globalMax = Math.max(...points.map(p => p.weight));

        list.innerHTML = `
            <div class="detail-row"><span class="detail-label">Active Hubs</span><span class="detail-value">${sortedHubs.length} Cities</span></div>
            <div class="detail-row"><span class="detail-label">Total Volume</span><span class="detail-value">${points.length} Bills</span></div>
            <div class="detail-row" style="margin-bottom: 20px;"><span class="detail-label">Peak Invoice</span><span class="detail-value">${formatCurrency(globalMax)}</span></div>
            
            <h5 style="font-size: 10px; color: var(--accent-orange); margin-bottom: 15px; text-transform: uppercase;">Location Breakdown</h5>
        `;

        sortedHubs.forEach((hub, i) => {
            // Find max invoice in this specific hub
            const hubInvoices = points.filter(p => p.city === hub.name);
            const hubMax = Math.max(...hubInvoices.map(p => p.weight));

            list.innerHTML += `
                <div class="detail-card" style="margin-bottom: 10px; padding: 12px; background: rgba(255,255,255,0.03);">
                    <div class="detail-row" style="margin-bottom: 5px;">
                        <span style="font-weight: 700; color: #fff;">${hub.name}</span>
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <span class="badge badge-paid">${hub.count} Bills</span>
                            <a href="/invoices?location=${encodeURIComponent(hub.name)}" style="font-size: 10px; color: var(--accent-orange); text-decoration: none; font-weight: 700; background: rgba(255,87,34,0.1); padding: 4px 8px; border-radius: 4px; letter-spacing: 0.5px;">VIEW BILLS</a>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Total Revenue</span>
                        <span class="detail-value">${formatCurrency(hub.revenue)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Highest Invoice</span>
                        <span class="detail-value">${formatCurrency(hubMax)}</span>
                    </div>
                </div>
            `;
        });
    }, 300);
}
