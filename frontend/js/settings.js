/**
 * Settings Page Logic
 * Handles fetching and saving company profile data.
 */

let currentBankAccounts = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth()) return;
    setNavUsername();
    
    // Save Changes Listener
    const saveBtn = document.getElementById('saveBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveProfile);
    }
    
    // RBAC: Hide Org Settings for non-admins
    const userData = sessionStorage.getItem('user_data');
    const user = userData ? JSON.parse(userData) : null;
    
    if (user && user.role !== 'admin') {
        if (saveBtn) saveBtn.style.display = 'none';
        // Make fields readonly for users
        const fields = ['company_name', 'address', 'gstin', 'pan', 'phone'];
        fields.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.readOnly = true;
        });
        const addBankBtn = document.getElementById('btnAddBank');
        if (addBankBtn) addBankBtn.style.display = 'none';
        
        // Hide Custom Branding section for non-admins
        const aiBrandingSection = document.getElementById('aiBrandingSection');
        if (aiBrandingSection) aiBrandingSection.style.display = 'none';
    }

    document.getElementById('btnAddBank').addEventListener('click', () => {
        addBankFormRow();
    });
    
    await loadProfile();

    // Delete Account Steps Logic (Confirmation input logic)
    const deleteBtn = document.getElementById('btnDeleteAccount');
    const confirmInput = document.getElementById('deleteConfirmInput');

    if (confirmInput) {
        confirmInput.addEventListener('input', (e) => {
            const userEmail = document.getElementById('email').value.trim();
            const companyName = document.getElementById('company_name').value.trim();
            const val = e.target.value.trim();
            
            // Enable button if input matches email OR company name exactly
            if (val === userEmail || val === companyName) {
                deleteBtn.disabled = false;
                deleteBtn.style.cursor = 'pointer';
                deleteBtn.style.background = 'rgba(255,59,48,0.1)';
            } else {
                deleteBtn.disabled = true;
                deleteBtn.style.cursor = 'not-allowed';
                deleteBtn.style.background = 'rgba(255,59,48,0.05)';
            }
        });
    }

    const deleteModal = document.getElementById('deleteModal');
    const cancelDelete = document.getElementById('btnCancelDelete');
    const confirmDelete = document.getElementById('btnConfirmDelete');

    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            if (!deleteBtn.disabled) {
                document.getElementById('deleteModal').style.display = 'flex';
            }
        });
    }

    if (cancelDelete) {
        cancelDelete.addEventListener('click', () => {
            deleteModal.style.display = 'none';
        });
    }

    if (confirmDelete) {
        confirmDelete.addEventListener('click', async () => {
            await deleteAccount();
        });
    }

    // ── AI Design Engine Logic ──────────────────────────────────
    initDesignEngine();
});

async function initDesignEngine() {
    const dropZone = document.getElementById('designDropZone');
    const fileInput = document.getElementById('designFileInput');
    const preview = document.getElementById('designTokensPreview');
    const tokensGrid = document.getElementById('tokensGrid');
    const btnConfirm = document.getElementById('btnConfirmDesign');
    const btnCancel = document.getElementById('btnCancelDesign');
    const statusLabel = document.getElementById('brandingStatus');
    const btnResetGlobal = document.getElementById('btnResetToDefault');

    // 1. Fetch current design status
    try {
        const design = await ApiClient.getActiveDesign();
        if (design && design.status === 'custom') {
            statusLabel.innerText = 'AI CUSTOM ACTIVE';
            statusLabel.className = 'badge badge-pending';
            statusLabel.style.display = 'inline-block';
            if (btnResetGlobal) btnResetGlobal.style.display = 'inline-block';
        } else {
            statusLabel.innerText = 'SYSTEM DEFAULT';
            statusLabel.className = 'badge badge-draft';
            if (btnResetGlobal) btnResetGlobal.style.display = 'none';
        }
    } catch (e) {
        if (btnResetGlobal) btnResetGlobal.style.display = 'none';
    }

    // Global Reset Logic
    btnResetGlobal.onclick = async () => {
        if (confirm('Are you sure you want to delete your custom format and return to default?')) {
            try {
                await ApiClient.resetDesign();
                showToast('Returned to system default style.', 'success');
                setTimeout(() => window.location.reload(), 1500);
            } catch (e) {
                showToast(e.message, 'error');
            }
        }
    };

    // 2. Click to trigger file input
    dropZone.onclick = () => fileInput.click();

    // 3. Handle File selection
    fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        await handleDesignUpload(file);
    };

    // 4. Handle Drag & Drop
    dropZone.ondragover = (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--accent-orange)';
        dropZone.style.background = 'rgba(255, 87, 34, 0.1)';
    };

    dropZone.ondragleave = () => {
        dropZone.style.borderColor = 'rgba(255, 87, 34, 0.3)';
        dropZone.style.background = 'transparent';
    };

    dropZone.ondrop = async (e) => {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        if (file) await handleDesignUpload(file);
    };

    async function handleDesignUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            dropZone.innerHTML = `<div class="spinner" style="margin-bottom: 12px;"></div><div style="font-size: 13px; color: var(--text-primary);">AI ANALYZING STYLE...</div>`;
            
            const result = await ApiClient.analyzeDesign(formData);
            
            // Render Tokens
            tokensGrid.innerHTML = '';
            for (const [key, value] of Object.entries(result.tokens)) {
                const label = key.replace(/_/g, ' ').toUpperCase();
                const div = document.createElement('div');
                div.style.padding = '10px';
                div.style.background = 'rgba(0,0,0,0.2)';
                div.style.borderRadius = '4px';
                div.innerHTML = `
                    <div style="font-size: 9px; color: var(--text-secondary); margin-bottom: 4px;">${label}</div>
                    <div style="font-size: 11px; font-weight: 700; color: var(--text-primary);">${value}</div>
                `;
                tokensGrid.appendChild(div);
            }

            preview.style.display = 'block';
            dropZone.style.display = 'none';
            showToast('AI style extraction complete!', 'success');

        } catch (e) {
            showToast(e.message, 'error');
            resetUI();
        }
    }

    function resetUI() {
        dropZone.style.display = 'block';
        preview.style.display = 'none';
        dropZone.innerHTML = `
            <div style="font-size: 32px; margin-bottom: 12px;">📸</div>
            <div style="font-size: 13px; font-weight: 700; color: var(--text-primary);">DROP SAMPLE INVOICE</div>
            <div style="font-size: 10px; color: var(--text-secondary); margin-top: 8px;">PNG, JPG, or PDF (Max 5MB)</div>
        `;
    }

    btnCancel.onclick = resetUI;
    btnConfirm.onclick = () => {
        showToast('Style applied! Your next invoice will use this design.', 'success');
        setTimeout(() => window.location.reload(), 1500);
    };
}

async function loadProfile() {
    try {
        const profile = await ApiClient.getProfile();
        
        // Populate fields
        document.getElementById('company_name').value = profile.company_name || '';
        document.getElementById('address').value = profile.address || '';
        document.getElementById('country').value = profile.country || 'India';
        document.getElementById('gstin').value = profile.gstin || '';
        document.getElementById('vat_number').value = profile.vat_number || '';
        document.getElementById('pan').value = profile.pan || '';
        document.getElementById('email').value = profile.email || '';
        document.getElementById('phone').value = profile.phone || '';
        
        currentBankAccounts = profile.bank_accounts || [];
        renderBankAccounts();
        
    } catch (error) {
        console.error('Failed to load profile:', error);
        showToast('Failed to load profile details', 'error');
    }
}

function renderBankAccounts() {
    const container = document.getElementById('bankAccountsContainer');
    container.innerHTML = '';
    currentBankAccounts.forEach((bank, index) => addBankFormRow(bank, index));
}

function addBankFormRow(bank = null, index = null) {
    const container = document.getElementById('bankAccountsContainer');
    const idx = index !== null ? index : document.querySelectorAll('.bank-account-item').length;
    
    const div = document.createElement('div');
    div.className = 'bank-account-item';
    div.style.marginBottom = '16px';
    div.style.padding = '16px';
    div.style.background = 'rgba(0,0,0,0.2)';
    div.style.borderRadius = 'var(--radius-md)';
    div.style.position = 'relative';
    
    div.innerHTML = `
        <button type="button" class="btn-remove-bank" style="position: absolute; top: 12px; right: 12px; background: none; border: none; color: var(--accent-red); cursor: pointer;">Remove</button>
        <div class="row" style="margin-bottom: 8px;">
            <div class="input-group">
                <label>Bank Name</label>
                <input type="text" class="b-name" value="${bank?.bank_name || ''}" placeholder="Global Tech Bank">
            </div>
            <div class="input-group">
                <label>Account Name</label>
                <input type="text" class="b-acc-name" value="${bank?.account_name || ''}" placeholder="John Doe">
            </div>
        </div>
        <div class="row">
            <div class="input-group">
                <label>Account Number</label>
                <input type="text" class="b-acc-no" value="${bank?.account_no || ''}" placeholder="0000 1111 2222">
            </div>
            <div class="input-group">
                <label>IFSC Code</label>
                <input type="text" class="b-ifsc" value="${bank?.ifsc || ''}" placeholder="TECH0000123">
            </div>
        </div>
    `;
    
    div.querySelector('.btn-remove-bank').addEventListener('click', () => {
        div.remove();
    });
    
    container.appendChild(div);
}

async function saveProfile() {
    const saveBtn = document.getElementById('saveBtn');
    const originalText = saveBtn.innerText;
    
    // Collect bank accounts
    const bankItems = document.querySelectorAll('.bank-account-item');
    const bank_accounts = [];
    bankItems.forEach(item => {
        const b_name = item.querySelector('.b-name').value.trim();
        const b_acc_name = item.querySelector('.b-acc-name').value.trim();
        const b_acc_no = item.querySelector('.b-acc-no').value.trim();
        const b_ifsc = item.querySelector('.b-ifsc').value.trim();
        
        if (b_name || b_acc_name || b_acc_no || b_ifsc) {
            bank_accounts.push({
                bank_name: b_name,
                account_name: b_acc_name,
                account_no: b_acc_no,
                ifsc: b_ifsc
            });
        }
    });
    
    // Collect data
    const profileData = {
        company_name: document.getElementById('company_name').value.trim(),
        address: document.getElementById('address').value.trim(),
        country: document.getElementById('country').value.trim(),
        gstin: document.getElementById('gstin').value.trim(),
        vat_number: document.getElementById('vat_number').value.trim(),
        pan: document.getElementById('pan').value.trim(),
        email: document.getElementById('email').value.trim(),
        phone: document.getElementById('phone').value.trim(),
        bank_accounts: bank_accounts
    };

    // Validation
    if (!profileData.company_name || !profileData.email) {
        showToast('Please fill in all required fields (Name, Email)', 'error');
        return;
    }

    try {
        saveBtn.innerText = 'Saving...';
        saveBtn.disabled = true;
        
        await ApiClient.updateProfile(profileData);
        
        showToast('Company profile updated successfully!', 'success');
        
    } catch (error) {
        console.error('Failed to save profile:', error);
        showToast('Failed to save profile. Please try again.', 'error');
    } finally {
        saveBtn.innerText = originalText;
        saveBtn.disabled = false;
    }
}
async function deleteAccount() {
    const confirmBtn = document.getElementById('btnConfirmDelete');
    const passwordInput = document.getElementById('deletePasswordConfirm');
    const originalText = confirmBtn.innerText;

    const password = passwordInput.value;
    if (!password) {
        showToast('Password is required for confirmation', 'error');
        return;
    }

    try {
        confirmBtn.innerText = 'Verifying...';
        confirmBtn.disabled = true;

        await ApiClient.deleteSelf(password);
        
        showToast('Account successfully deleted.', 'success');
        
        // Immediate cleanup
        sessionStorage.clear();
        sessionStorage.clear();
        
        // Delay redirect slightly to show toast
        setTimeout(() => {
            window.location.href = '/login?msg=account_deleted';
        }, 1500);

    } catch (error) {
        console.error('Deletion Failed:', error);
        // Error message is already toasted by ApiClient
        confirmBtn.innerText = originalText;
        confirmBtn.disabled = false;
        document.getElementById('deleteModal').style.display = 'none';
        passwordInput.value = '';
    }
}
