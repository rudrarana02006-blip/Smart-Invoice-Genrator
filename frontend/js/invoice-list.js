/**
 * Invoice List Logic
 * Handles fetching, filtering, pagination, and rendering of invoices on the management page.
 */

let currentPage = 1;
const perPage = 10;
let totalPages = 1;
let currentSearch = '';
let currentLocation = '';

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    setNavUsername();
    
    // Check for location filter in URL
    const urlParams = new URLSearchParams(window.location.search);
    currentLocation = urlParams.get('location') || '';
    
    if (currentLocation) {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.placeholder = `Filtering by: ${currentLocation}...`;
        }
    }
    
    // Setup Search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce((e) => {
            currentSearch = e.target.value.trim();
            currentPage = 1; // Reset to first page on search
            loadInvoices();
        }, 500));
    }
    
    // Setup Pagination Buttons
    document.getElementById('btnPrevPage').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadInvoices();
        }
    });
    
    document.getElementById('btnNextPage').addEventListener('click', () => {
        // We increment assuming there might be more. The API handles empty returns.
        currentPage++;
        loadInvoices();
    });

    loadInvoices();
});

async function loadInvoices() {
    const container = document.getElementById('invoiceList');
    container.innerHTML = `
        <div class="invoice-row glass-panel hover-specular">
            <div class="skeleton skeleton-text" style="width: 80%;"></div>
            <div class="skeleton skeleton-text" style="width: 60%;"></div>
            <div class="skeleton skeleton-text" style="width: 90%;"></div>
            <div class="skeleton skeleton-text" style="width: 40%;"></div>
        </div>
        <div class="invoice-row glass-panel hover-specular">
            <div class="skeleton skeleton-text" style="width: 70%;"></div>
            <div class="skeleton skeleton-text" style="width: 50%;"></div>
            <div class="skeleton skeleton-text" style="width: 80%;"></div>
            <div class="skeleton skeleton-text" style="width: 30%;"></div>
        </div>
    `;
    
    try {
        const skip = (currentPage - 1) * perPage;
        const invoices = await ApiClient.getInvoices(skip, perPage, currentSearch, currentLocation);
        
        renderInvoices(invoices);
        updatePaginationState(invoices.length);
        
    } catch (e) {
        container.innerHTML = `<div style="text-align: center; padding: 40px; color: #ff3b30;">Failed to load invoices.</div>`;
    }
}

function renderInvoices(invoices) {
    const container = document.getElementById('invoiceList');
    const user = JSON.parse(sessionStorage.getItem('user_data') || '{}');
    const isAdmin = user.role === 'admin';
    
    // Hide column if not admin
    const colGeneratedBy = document.getElementById('colGeneratedBy');
    const listHeader = document.getElementById('listHeader');
    if (!isAdmin) {
        if (colGeneratedBy) colGeneratedBy.style.display = 'none';
        if (listHeader) listHeader.style.gridTemplateColumns = '1fr 2fr 1fr 1fr auto';
    }

    if (!invoices || invoices.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                No invoices found.
            </div>`;
        return;
    }
    
    container.innerHTML = invoices.map(inv => {
        const rowStyle = isAdmin ? 'grid-template-columns: 1fr 2fr 1fr 1fr 1.2fr auto;' : 'grid-template-columns: 1fr 2fr 1fr 1fr auto;';
        return `
        <div class="invoice-row glass-panel" style="margin-bottom: 8px; ${rowStyle}">
            <div class="invoice-number">${inv.invoice_number}</div>
            <div class="invoice-client">
                <div>${inv.client_name}</div>
                <div style="font-size: 12px; color: var(--text-secondary);">${inv.client_email}</div>
            </div>
            <div>
                <span class="badge badge-${inv.status}">${inv.status}</span>
            </div>
            <div class="invoice-amount">${formatCurrency(inv.grand_total, inv.currency)}</div>
            ${isAdmin ? `<div style="text-align: center; font-size: 12px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${inv.created_by_email || 'System'}</div>` : ''}
            <div style="display: flex; gap: 12px; justify-content: center;">
                <button onclick="cloneInvoice('${inv._id}')" class="action-btn" data-tooltip="CLONE / RECUR" style="color: var(--accent-orange);">📁</button>
                <button onclick="downloadPdf('${inv._id}')" class="action-btn" data-tooltip="DOWNLOAD PDF">📄</button>
                <button onclick="sendAIEmail('${inv._id}')" class="action-btn email-btn-${inv._id}" data-tooltip="AI DISPATCH & CC ADMIN">✉️</button>
                ${inv.status === 'paid' ? 
                    `<button onclick="updateStatus('${inv._id}', 'pending')" class="action-btn" data-tooltip="MARK AS UNPAID" style="color: var(--accent-orange);">🔄</button>` : 
                    `<button onclick="updateStatus('${inv._id}', 'paid')" class="action-btn" data-tooltip="MARK AS PAID">💰</button>`
                }
                ${inv.status !== 'draft' ? 
                    `<button onclick="updateStatus('${inv._id}', 'draft')" class="action-btn" data-tooltip="REVERT TO DRAFT" style="opacity: 0.5;">📁</button>` : 
                    ''
                }
                <button onclick="deleteInvoice('${inv._id}')" class="action-btn" style="background: rgba(255,59,48,0.1); color: #ff3b30;" data-tooltip="DELETE INVOICE">🗑️</button>
            </div>
        </div>
        `;
    }).join('');
}

function updatePaginationState(returnedCount) {
    const btnPrev = document.getElementById('btnPrevPage');
    const btnNext = document.getElementById('btnNextPage');
    
    btnPrev.disabled = currentPage === 1;
    // If we received fewer items than requested, we are on the last page
    btnNext.disabled = returnedCount < perPage;
}

// Action Handlers
async function updateStatus(id, newStatus) {
    if (!confirm(`Mark invoice as ${newStatus}?`)) return;
    
    try {
        await ApiClient.updateInvoiceStatus(id, newStatus);
        showToast(`Invoice marked as ${newStatus}`);
        loadInvoices(); // Reload
    } catch (e) {
        // Error handled by ApiClient
    }
}

async function deleteInvoice(id) {
    if (!confirm('Are you sure you want to delete this invoice? This cannot be undone.')) return;
    
    try {
        await ApiClient.deleteInvoice(id);
        showToast('Invoice deleted successfully');
        loadInvoices(); // Reload
    } catch (e) {
        // Error handled by ApiClient
    }
}

async function downloadPdf(id) {
    const isComplete = await checkProfileStatus();
    if (!isComplete) {
        showProfileGate();
        return;
    }

    const btn = document.querySelector(`button[onclick="downloadPdf('${id}')"]`);
    if (btn) {
        const originalText = btn.innerHTML;
        btn.innerHTML = '⏳';
        btn.disabled = true;
        
        await ApiClient.downloadPdf(id);
        
        btn.innerHTML = originalText;
        btn.disabled = false;
    } else {
        await ApiClient.downloadPdf(id);
    }
}
async function sendAIEmail(id) {

    const isComplete = await checkProfileStatus();
    if (!isComplete) {
        showProfileGate();
        return;
    }

    const btn = document.querySelector(`.email-btn-${id}`);
    if (!btn) return;

    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="loading-spinner-tiny"></span>';
    btn.disabled = true;

    showToast('Gemini is drafting & CC\'ing Admin...', 'info');

    try {
        const result = await ApiClient.sendInvoiceEmail(id);
        showToast(`Invoice dispatched! Admin (${result.cc_admin}) has been CC’d.`, 'success');
        loadInvoices(); // Refresh to show 'sent' status
    } catch (e) {
        console.error('Email Error:', e);
        // Error toast shown by ApiClient
    } finally {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    }
}
async function cloneInvoice(id) {
    if (!confirm('Clone this invoice to create a new draft?')) return;
    
    showToast('Cloning invoice...', 'info');
    try {
        const newInvoice = await ApiClient.cloneInvoice(id);
        showToast('Invoice cloned! Opening draft...', 'success');
        // Redirect to edit/create page for the new invoice? 
        // Or just reload list? Cloned invoices are drafts.
        loadInvoices();
    } catch (e) {
        // Error handled by ApiClient
    }
}
