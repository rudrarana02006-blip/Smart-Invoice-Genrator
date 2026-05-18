/**
 * Organization Management Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    setNavUsername();
    
    // Check if admin
    const user = JSON.parse(sessionStorage.getItem('user_data') || '{}');
    if (user.role !== 'admin') {
        window.location.href = '/';
        return;
    }

    loadUsers();
    loadProfile();

    // Profile saving
    const saveBtn = document.getElementById('saveProfileBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveProfile);
    }

    // Reset Design
    const resetBtn = document.getElementById('resetDesignBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', async () => {
            if (!confirm("Are you sure you want to delete your custom invoice design and return to the default monochromatic theme?")) return;
            try {
                resetBtn.textContent = 'Resetting...';
                await ApiClient.resetDesign();
                showToast("Design reset to default. Refreshing...");
                setTimeout(() => window.location.reload(), 1500);
            } catch (e) {
                showToast("Failed to reset design", true);
                resetBtn.textContent = 'Reset Design';
            }
        });
    }
});

async function loadProfile() {
    try {
        const profile = await ApiClient.getProfile();
        if (profile) {
            const form = document.getElementById('profileForm');
            // Basic Info
            form.company_name.value = profile.company_name || '';
            form.company_tagline.value = profile.company_tagline || '';
            form.email.value = profile.email || '';
            form.phone.value = profile.phone || '';
            form.address.value = profile.address || '';
            form.gstin.value = profile.gstin || '';
            form.pan.value = profile.pan || '';
            form.website.value = profile.website || '';
            
            // Bank Info (Flattened for the simple UI)
            form.bank_name.value = profile.bank_name || '';
            form.bank_account.value = profile.bank_account || '';
            form.bank_ifsc.value = profile.bank_ifsc || '';
            form.bank_account_name.value = profile.bank_account_name || profile.company_name || '';
        }
    } catch (e) {
        console.error("Failed to load profile:", e);
    }
}

async function saveProfile() {
    const btn = document.getElementById('saveProfileBtn');
    const originalText = btn.textContent;
    btn.textContent = 'Saving...';
    btn.disabled = true;

    try {
        const form = document.getElementById('profileForm');
        const profileData = {
            company_name: form.company_name.value,
            company_tagline: form.company_tagline.value,
            email: form.email.value,
            phone: form.phone.value,
            address: form.address.value,
            gstin: form.gstin.value,
            pan: form.pan.value,
            website: form.website.value,
            bank_name: form.bank_name.value,
            bank_account: form.bank_account.value,
            bank_ifsc: form.bank_ifsc.value,
            bank_account_name: form.bank_account_name.value
        };

        await ApiClient.updateProfile(profileData);
        showToast("Profile updated successfully!");
    } catch (e) {
        showToast("Failed to update profile", true);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

async function loadUsers() {
    const container = document.getElementById('userList');
    container.innerHTML = `<div style="text-align: center; padding: 20px;">Loading team...</div>`;
    
    try {
        const users = await ApiClient.getOrgUsers();
        renderUsers(users);
    } catch (e) {
        container.innerHTML = `<div style="text-align: center; padding: 20px; color: #ff3b30;">Failed to load users.</div>`;
    }
}

function renderUsers(users) {
    const container = document.getElementById('userList');
    
    if (!users || users.length === 0) {
        container.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--text-secondary);">No other users found.</div>`;
        return;
    }
    
    container.innerHTML = users.map(u => {
        const isAdmin = u.role === 'admin';
        return `
        <div class="user-row glass-panel ${isAdmin ? 'admin-row' : ''}" style="margin-bottom: 8px;" id="user-${u.id}">
            <div style="font-weight: 500;">${u.email}</div>
            <div style="text-transform: uppercase; font-size: 10px; font-weight: 600; color: ${isAdmin ? 'var(--accent-orange)' : 'var(--text-secondary)'};">
                ${u.role} ${isAdmin ? '★' : ''}
            </div>
            <div class="status-cell">
                <span class="status-badge ${u.status === 'approved' ? 'status-approved' : 'status-pending'}">
                    ${u.status.toUpperCase()}
                </span>
            </div>
            <div class="actions-cell" style="display: flex; gap: 8px; justify-content: center; width: 150px;">
                ${isAdmin ? `
                    <span style="font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px;">System Owner</span>
                ` : `
                    <button onclick="toggleUserStatus('${u.id}', '${u.email}')" class="btn-toggle ${u.status === 'approved' ? 'btn-revoke' : 'btn-approve'}">
                        ${u.status === 'approved' ? 'Revoke Access' : 'Approve Access'}
                    </button>
                    <button onclick="deleteUser('${u.id}', '${u.email}')" class="btn-delete-staff" title="Permanently Delete User">
                        <i class="fas fa-trash"></i>
                    </button>
                `}
            </div>
        </div>
        `;
    }).join('');
    
    // Add dynamic styles if not present
    if (!document.getElementById('org-dynamic-styles')) {
        const style = document.createElement('style');
        style.id = 'org-dynamic-styles';
        style.textContent = `
            .admin-row {
                border: 1px solid rgba(255, 149, 0, 0.3) !important;
                background: linear-gradient(90deg, rgba(255, 149, 0, 0.05) 0%, transparent 100%) !important;
                box-shadow: 0 0 15px rgba(255, 149, 0, 0.05);
            }
            .status-badge {
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 700;
                font-family: 'JetBrains Mono', monospace;
                border: 1px solid transparent;
                transition: all 0.3s ease;
            }
            .status-approved {
                color: #34c759;
                border-color: rgba(52, 199, 89, 0.3);
                background: rgba(52, 199, 89, 0.05);
                box-shadow: 0 0 10px rgba(52, 199, 89, 0.1);
            }
            .status-pending {
                color: #ff9500;
                border-color: rgba(255, 149, 0, 0.3);
                background: rgba(255, 149, 0, 0.05);
            }
            .btn-toggle {
                background: transparent;
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                font-size: 10px;
                font-weight: 600;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.2s ease;
                text-transform: uppercase;
            }
            .btn-toggle:hover {
                background: var(--card-bg);
                border-color: var(--accent-color);
            }
            .btn-revoke {
                color: #ff3b30;
                border-color: rgba(255, 59, 48, 0.2);
            }
            .btn-revoke:hover {
                background: rgba(255, 59, 48, 0.05);
                border-color: #ff3b30;
                box-shadow: 0 0 15px rgba(255, 59, 48, 0.1);
            }
            .btn-approve {
                color: #34c759;
                border-color: rgba(52, 199, 89, 0.2);
            }
            .btn-approve:hover {
                background: rgba(52, 199, 89, 0.05);
                border-color: #34c759;
            }
            .btn-delete-staff {
                background: transparent;
                border: 1px solid rgba(255, 59, 48, 0.2);
                color: #ff3b30;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .btn-delete-staff:hover {
                background: #ff3b30;
                color: #fff;
                border-color: #ff3b30;
                box-shadow: 0 0 15px rgba(255, 59, 48, 0.3);
            }
        `;
        document.head.appendChild(style);
    }
}

async function toggleUserStatus(userId, email) {
    const rowId = `user-${userId}`;
    const row = document.getElementById(rowId);
    const btn = row.querySelector('.btn-toggle');
    const badge = row.querySelector('.status-badge');
    
    const originalText = btn.textContent;
    btn.textContent = '...';
    btn.disabled = true;
    
    try {
        const response = await ApiClient.toggleUserStatus(userId);
        const newStatus = response.new_status;
        
        // Update Badge
        badge.textContent = newStatus.toUpperCase();
        badge.className = `status-badge status-${newStatus}`;
        
        // Update Button
        btn.textContent = newStatus === 'approved' ? 'Revoke Access' : 'Approve Access';
        btn.className = `btn-toggle ${newStatus === 'approved' ? 'btn-revoke' : 'btn-approve'}`;
        
        showToast(`Access ${newStatus === 'approved' ? 'granted' : 'revoked'} for ${email}`);
    } catch (e) {
        btn.textContent = originalText;
    } finally {
        btn.disabled = false;
    }
}

async function approveUser(email) {
    // Legacy support for any existing calls, though we use toggle now
    await toggleUserStatus(email);
}

async function rejectUser(email) {
    if (!confirm(`Permanently remove user ${email}?`)) return;
    try {
        await ApiClient.rejectUser(email);
        showToast(`User ${email} removed`);
        loadUsers();
    } catch (e) {}
}

async function deleteUser(userId, email) {
    if (!confirm(`ARE YOU ABSOLUTELY SURE?\n\nThis will permanently delete the account for ${email}. This action cannot be undone.`)) return;
    
    const row = document.getElementById(`user-${userId}`);
    const originalContent = row.innerHTML;
    row.style.opacity = '0.5';
    row.style.pointerEvents = 'none';
    
    try {
        await ApiClient.adminDeleteUser(userId);
        showToast(`User ${email} has been permanently deleted.`);
        row.remove();
        
        // If list is empty now
        const container = document.getElementById('userList');
        if (container.children.length === 0) {
            container.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--text-secondary);">No other users found.</div>`;
        }
    } catch (e) {
        row.style.opacity = '1';
        row.style.pointerEvents = 'auto';
        // Error already toasted by ApiClient
    }
}
