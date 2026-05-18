/**
 * Utility functions — formatters, helpers, toast notifications.
 */

/** Currency symbols map */
const CURRENCY_SYMBOLS = {
    INR: '₹', USD: '$', EUR: '€', GBP: '£',
    AED: 'د.إ', CAD: 'C$', AUD: 'A$', JPY: '¥',
};

/** Format currency amounts */
function formatCurrency(amount, currency = 'INR') {
    const symbol = CURRENCY_SYMBOLS[currency] || currency;
    return `${symbol} ${Number(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })}`;
}

/** Format dates beautifully */
function formatDate(isoString) {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/** Nothing Tech Toast System */
function showToast(message, type = 'success', countdown = 0) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    // Process Message
    let displayMessage = message;
    if (typeof message === 'object' && message !== null) {
        displayMessage = message.detail || message.message || JSON.stringify(message);
    }

    // Split into first sentence and the rest
    const parts = displayMessage.split(/([.!?])\s/);
    let summary = displayMessage;
    let fullText = '';

    if (parts.length > 1) {
        summary = parts[0] + parts[1]; // "Sentence" + "."
        fullText = displayMessage.substring(summary.length).trim();
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-type-${type}`;
    
    toast.innerHTML = `
        <div class="toast-header">
            <div class="toast-icon"></div>
            <span class="toast-title">${type === 'success' ? 'STATUS: OK' : 'STATUS: ALERT'}</span>
            <button class="toast-close">✕</button>
        </div>
        <div class="toast-body">
            <span class="toast-summary">${summary}</span>
            ${fullText ? `<div class="toast-full-text">${fullText}</div>` : ''}
        </div>
        ${fullText ? `
            <div class="toast-footer">
                <button class="btn-read-more">READ MORE</button>
            </div>
        ` : ''}
    `;

    container.appendChild(toast);

    // Event Listeners
    const closeBtn = toast.querySelector('.toast-close');
    const readMoreBtn = toast.querySelector('.btn-read-more');
    let isPersistent = (type === 'error');

    const closeToast = () => {
        toast.style.animation = 'nothingSlideOut 0.4s cubic-bezier(0.19, 1, 0.22, 1) forwards';
        setTimeout(() => toast.remove(), 400);
    };

    closeBtn.addEventListener('click', closeToast);

    if (readMoreBtn) {
        readMoreBtn.addEventListener('click', () => {
            toast.classList.toggle('expanded');
            readMoreBtn.textContent = toast.classList.contains('expanded') ? 'SHOW LESS' : 'READ MORE';
            isPersistent = true; // Stay open if user interacts
        });
    }

    // Auto-remove logic
    if (!isPersistent) {
        setTimeout(() => {
            if (!toast.classList.contains('expanded')) {
                closeToast();
            }
        }, 5000);
    }
}

/** Auth Check */
function requireAuth() {
    const token = sessionStorage.getItem('token');
    const userData = sessionStorage.getItem('user_data');
    const user = userData ? JSON.parse(userData) : null;

    if (!token && window.location.pathname !== '/login') {
        window.location.href = '/login';
        return false;
    }

    // Role-based Access Control (RBAC)
    if (user && user.role !== 'admin') {
        const restrictedPaths = ['/org'];
        if (restrictedPaths.includes(window.location.pathname)) {
            // Immediately redirect to create invoice page
            window.location.href = '/create';
            return false;
        }
    }

    return true;
}

/** Logout */
function logout() {
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user_data');
    window.location.href = '/login';
}

async function setNavUsername() {
    let userData = sessionStorage.getItem('user_data');
    let user = {};
    
    if (userData && userData !== 'true') {
        try {
            user = JSON.parse(userData);
        } catch (e) {
            user = null;
        }
    }

    if (!user || !user.email) {
        // Force refresh if data is missing or corrupted
        if (sessionStorage.getItem('token')) {
            try {
                user = await ApiClient.request('/auth/me');
                sessionStorage.setItem('user_data', JSON.stringify(user));
            } catch (e) {
                return;
            }
        } else {
            return;
        }
    }

    const userNameElement = document.getElementById('userName');
    if (userNameElement && user.email) {
        const name = user.email.split('@')[0];
        const roleStr = user.role ? ` (${user.role.toUpperCase()})` : '';
        userNameElement.textContent = name + roleStr;
    }
    
    if (userAvatar && user.email) {
        userAvatar.textContent = user.email[0].toUpperCase();
        userAvatar.style.background = 'var(--accent-orange)';
    }
    
    // Manage Sidebar Links based on role
    const navLinks = document.querySelector('.nav-links');
    if (navLinks) {
        const path = window.location.pathname;
        
        // Add Organization link if admin
        if (user.role === 'admin' && !navLinks.querySelector('a[href="/org"]')) {
            const li = document.createElement('li');
            li.innerHTML = `<a href="/org">Organization</a>`;
            const settingsLi = Array.from(navLinks.querySelectorAll('li')).find(l => l.querySelector('a[href="/settings"]'));
            if (settingsLi) navLinks.insertBefore(li, settingsLi);
            else navLinks.appendChild(li);
        }

        // Set active class based on current path
        navLinks.querySelectorAll('a').forEach(link => {
            const href = link.getAttribute('href');
            if (href === path || (href === '/' && path === '') || (path === '/' && href === '/')) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }
}

/** Debounce function for search */
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

/** Theme logic */
(function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark-mode');
    } else {
        document.documentElement.classList.remove('dark-mode');
    }

    const toggleBtn = document.getElementById('themeToggle');
    if (!toggleBtn) return;
    
    toggleBtn.textContent = savedTheme === 'dark' ? 'LIGHT' : 'DARK';
    
    toggleBtn.addEventListener('click', () => {
        const isDark = document.documentElement.classList.toggle('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        toggleBtn.textContent = isDark ? 'LIGHT' : 'DARK';
    });
})();

/** Profile Gate Logic */
let profileStatusCache = null;

async function checkProfileStatus() {
    if (profileStatusCache !== null) return profileStatusCache;
    
    try {
        const profile = await ApiClient.getProfile();
        profileStatusCache = !!(profile && profile.company_name && profile.gstin);
        return profileStatusCache;
    } catch (e) {
        return false;
    }
}

function showProfileGate() {
    // Create Modal if it doesn't exist
    let modal = document.getElementById('profileGateModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'profileGateModal';
        modal.className = 'glass-modal-overlay';
        modal.innerHTML = `
            <div class="glass-modal-card hover-specular">
                <div class="modal-glow"></div>
                <div class="modal-icon">⚠️</div>
                <h3 class="modal-title">Wait!</h3>
                <p class="modal-text">To generate a legal invoice, we need your company details (Address, GST, etc.).</p>
                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="closeProfileGate()">Later</button>
                    <a href="/settings" class="btn btn-primary">Complete Profile</a>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Add Modal Styles
        const style = document.createElement('style');
        style.textContent = `
            .glass-modal-overlay {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(255, 255, 255, 0.2); backdrop-filter: blur(20px);
                display: flex; align-items: center; justify-content: center;
                z-index: 10000; animation: modalFadeIn 0.3s ease;
            }
            .dark-mode .glass-modal-overlay { background: rgba(0, 0, 0, 0.4); }
            
            .glass-modal-card {
                background: rgba(255, 255, 255, 0.4); border: 1px solid rgba(255, 255, 255, 0.5);
                border-radius: 24px; padding: 48px; width: 400px; text-align: center;
                position: relative; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            .dark-mode .glass-modal-card { background: rgba(25, 25, 25, 0.6); border: 1px solid rgba(255,255,255,0.1); }
            
            .modal-glow {
                position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
                background: radial-gradient(circle, rgba(255, 87, 34, 0.1) 0%, transparent 70%);
                pointer-events: none;
            }
            .modal-icon { font-size: 40px; margin-bottom: 24px; }
            .modal-title { font-family: 'NDot', sans-serif; font-size: 24px; margin-bottom: 12px; }
            .modal-text { font-size: 14px; color: var(--text-secondary); margin-bottom: 32px; line-height: 1.6; }
            .modal-actions { display: flex; gap: 16px; justify-content: center; }
            
            @keyframes modalFadeIn { from { opacity: 0; } to { opacity: 1; } }
        `;
        document.head.appendChild(style);
    }
    modal.style.display = 'flex';
}

function closeProfileGate() {
    const modal = document.getElementById('profileGateModal');
    if (modal) modal.style.display = 'none';
}

/** Page Transition Intercept (Event Delegation) */
document.addEventListener('click', async (e) => {
    const link = e.target.closest('a[href]');
    if (!link) return;

    const target = link.getAttribute('href');
    if (!target) return;

    // Handle profile gate for specific pages
    if (target === '/create') {
        const isComplete = await checkProfileStatus();
        if (!isComplete) {
            e.preventDefault();
            showProfileGate();
            return;
        }
    }

    // Handle local page transitions
    if (target.startsWith('/') && !link.hasAttribute('target') && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        document.body.classList.add('page-exit');
        setTimeout(() => {
            window.location.href = target;
        }, 300);
    }
});

async function syncActiveDesign() {
    try {
        const design = await ApiClient.getActiveDesign();
        if (design && design.status === 'custom' && design.tokens) {
            const primary = design.tokens.primary_color;
            if (primary) {
                // Apply ONLY to specific branded elements, not the whole UI
                document.querySelectorAll('.brand-reflect').forEach(el => {
                    el.style.borderColor = primary;
                    if (el.classList.contains('brand-text')) el.style.color = primary;
                });
            }
        }
    } catch (e) {
        console.warn("Design sync failed:", e);
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    await setNavUsername();
    await syncActiveDesign();
});
