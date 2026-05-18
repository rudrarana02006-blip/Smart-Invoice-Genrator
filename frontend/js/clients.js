/**
 * Client Management Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initial load
    fetchClients();

    // Event Listeners
    document.getElementById('btn-add-client').addEventListener('click', () => openClientModal());
    document.getElementById('client-form').addEventListener('submit', handleSaveClient);
    document.getElementById('client-search').addEventListener('input', debounce(handleSearch, 300));

    // Modal Close
    document.querySelectorAll('.close-modal, .close-modal-btn').forEach(btn => {
        btn.addEventListener('click', closeClientModal);
    });
});

let allClients = [];

async function fetchClients() {
    const loading = document.getElementById('clients-loading');
    const empty = document.getElementById('clients-empty');
    const grid = document.getElementById('clients-grid');

    loading.style.display = 'flex';
    empty.style.display = 'none';
    grid.innerHTML = '';

    try {
        const clients = await ApiClient.getClients();
        allClients = clients;
        renderClients(clients);
    } catch (e) {
        showToast('Failed to load clients', 'error');
    } finally {
        loading.style.display = 'none';
    }
}

function renderClients(clients) {
    const grid = document.getElementById('clients-grid');
    const empty = document.getElementById('clients-empty');
    
    grid.innerHTML = '';
    
    if (clients.length === 0) {
        empty.style.display = 'block';
        return;
    }

    empty.style.display = 'none';
    
    clients.forEach(client => {
        const initials = client.name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
        
        const card = document.createElement('div');
        card.className = 'client-card';
        card.innerHTML = `
            <div class="client-initials">${initials}</div>
            <h3 class="text-primary">${client.name}</h3>
            <p class="text-secondary small"><i class="fas fa-envelope mr-2"></i> ${client.email}</p>
            ${client.phone ? `<p class="text-secondary small"><i class="fas fa-phone mr-2"></i> ${client.phone}</p>` : ''}
            ${client.company_name ? `<p class="text-secondary small"><i class="fas fa-building mr-2"></i> ${client.company_name}</p>` : ''}
            
            <div class="client-actions">
                <button class="action-btn-small" onclick="openClientModal('${client._id}')" title="Edit Client">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="action-btn-small" onclick="createNewInvoiceForClient('${client._id}')" title="Create Invoice">
                    <i class="fas fa-file-invoice"></i>
                </button>
                <button class="action-btn-small delete" onclick="handleDeleteClient('${client._id}')" title="Delete Client">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        grid.appendChild(card);
    });
}

function handleSearch(e) {
    const term = e.target.value.toLowerCase();
    const filtered = allClients.filter(c => 
        c.name.toLowerCase().includes(term) || 
        c.email.toLowerCase().includes(term) || 
        (c.company_name && c.company_name.toLowerCase().includes(term))
    );
    renderClients(filtered);
}

function openClientModal(clientId = null) {
    const modal = document.getElementById('client-modal');
    const form = document.getElementById('client-form');
    const title = document.getElementById('modal-title');
    
    form.reset();
    document.getElementById('edit-client-id').value = clientId || '';
    
    if (clientId) {
        title.innerText = 'Edit Client';
        const client = allClients.find(c => c._id === clientId);
        if (client) {
            document.getElementById('client-name').value = client.name;
            document.getElementById('client-email').value = client.email;
            document.getElementById('client-phone').value = client.phone || '';
            document.getElementById('client-company').value = client.company_name || '';
            document.getElementById('client-gstin').value = client.gstin || '';
            document.getElementById('client-address').value = client.address || '';
            document.getElementById('default-cgst').value = client.default_cgst_rate || 0;
            document.getElementById('default-sgst').value = client.default_sgst_rate || 0;
        }
    } else {
        title.innerText = 'Add New Client';
    }
    
    modal.classList.add('active');
}

function closeClientModal() {
    document.getElementById('client-modal').classList.remove('active');
}

async function handleSaveClient(e) {
    e.preventDefault();
    const clientId = document.getElementById('edit-client-id').value;
    const clientData = {
        name: document.getElementById('client-name').value,
        email: document.getElementById('client-email').value,
        phone: document.getElementById('client-phone').value || null,
        company_name: document.getElementById('client-company').value || null,
        gstin: document.getElementById('client-gstin').value || null,
        address: document.getElementById('client-address').value || null,
        default_cgst_rate: parseFloat(document.getElementById('default-cgst').value) || 0,
        default_sgst_rate: parseFloat(document.getElementById('default-sgst').value) || 0
    };

    const btn = document.getElementById('btn-save-client');
    btn.disabled = true;
    btn.innerText = 'Saving...';

    try {
        if (clientId) {
            await ApiClient.updateClient(clientId, clientData);
            showToast('Client updated successfully');
        } else {
            await ApiClient.createClient(clientData);
            showToast('Client added successfully');
        }
        closeClientModal();
        fetchClients();
    } catch (e) {
        showToast(e.message || 'Error saving client', 'error');
    } finally {
        btn.disabled = false;
        btn.innerText = 'Save Client';
    }
}

async function handleDeleteClient(clientId) {
    if (!confirm('Are you sure you want to delete this client? This action cannot be undone.')) return;
    
    try {
        await ApiClient.deleteClient(clientId);
        showToast('Client deleted');
        fetchClients();
    } catch (e) {
        showToast('Failed to delete client', 'error');
    }
}

function createNewInvoiceForClient(clientId) {
    const client = allClients.find(c => c._id === clientId);
    if (client) {
        // We can pass client data via session storage to the create page
        sessionStorage.setItem('prefill_client', JSON.stringify(client));
        window.location.href = '/create';
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
