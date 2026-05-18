/**
 * API Client — Centralized fetch wrapper for all backend calls.
 * Handles authentication, error handling, and token management.
 */

const API_BASE = '/api';

class ApiClient {
    static getToken() {
        return sessionStorage.getItem('token');
    }

    static async request(endpoint, options = {}) {
        const token = this.getToken();
        
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                ...options,
                headers
            });
            
            console.log(`DEBUG: [${options.method || 'GET'}] ${endpoint} Status:`, response.status);
            
            let data = null;
            if (response.status !== 204) {
                try {
                    data = await response.json();
                } catch (e) {
                    console.error("DEBUG: Failed to parse JSON response");
                }
            }

            if (response.status === 401 && window.location.pathname !== '/login') {
                logout();
                return null;
            }

            if (response.status === 403) {
                const detail = (data && data.detail) || '';
                if (detail.toLowerCase().includes('pending') || detail.toLowerCase().includes('approved')) {
                    document.body.innerHTML = `
                        <div style="height: 100vh; display: flex; align-items: center; justify-content: center; background: #000; color: #fff; flex-direction: column; text-align: center; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                            <div style="font-size: 48px; margin-bottom: 30px; color: #ff3b30;">●</div>
                            <h1 style="font-family: 'NDot', sans-serif; font-size: 32px; letter-spacing: 2px;">ACCESS REVOKED</h1>
                            <p style="color: #888; margin-top: 20px; max-width: 400px; line-height: 1.6;">Your account status is currently <b>PENDING</b>. You need an administrator to approve your access before you can continue.</p>
                            <div style="margin-top: 40px; display: flex; gap: 16px;">
                                <a href="/login" onclick="sessionStorage.clear(); sessionStorage.clear()" style="color: #fff; text-decoration: none; border: 1px solid #333; padding: 12px 24px; border-radius: 8px; font-size: 14px; font-weight: 600; transition: all 0.2s ease;">Logout</a>
                                <button onclick="window.location.reload()" style="background: #fff; color: #000; border: none; padding: 12px 24px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer;">Check Again</button>
                            </div>
                        </div>
                    `;
                    document.body.style.background = '#000';
                    return null;
                }
            }
            
            if (response.status === 204) {
                return true;
            }
            
            if (!response.ok || (data && data.error)) {
                let errorMsg = (data && data.error) || (data && data.detail) || response.statusText || 'API Request Failed';
                if (data && data.detail && Array.isArray(data.detail)) {
                    errorMsg = data.detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
                }
                showToast(errorMsg, 'error');
                throw new Error(errorMsg);
            }
            
            return data;
        } catch (error) {
            throw error;
        }
    }

    // --- Auth ---
    static async requestOtp(email) {
        return this.request('/auth/request-otp', {
            method: 'POST',
            body: JSON.stringify({ email })
        });
    }

    static async verifyOtp(email, otp) {
        return this.request('/auth/verify-otp', {
            method: 'POST',
            body: JSON.stringify({ email, otp })
        });
    }

    static async setPassword(email, password, token, role = 'admin', adminEmail = null, registrationData = {}) {
        return this.request('/auth/set-password', {
            method: 'POST',
            body: JSON.stringify({ 
                email, 
                password, 
                token, 
                role, 
                admin_email: adminEmail,
                registration_data: registrationData
            })
        });
    }

    static async forgotPassword(email) {
        return this.request('/auth/forgot-password', {
            method: 'POST',
            body: JSON.stringify({ email })
        });
    }

    static async resetPassword(email, otp, newPassword) {
        return this.request('/auth/reset-password', {
            method: 'POST',
            body: JSON.stringify({ email, otp, new_password: newPassword })
        });
    }

    static async checkUser(email) {
        return this.request(`/auth/check-user/${encodeURIComponent(email)}`);
    }

    static async login(email, password, expectedRole = null) {
        try {
            const response = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    username: email, 
                    password: password,
                    expected_role: expectedRole 
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                showToast(error.detail || 'Login Failed', 'error');
                return null;
            }
            
            const data = await response.json();
            sessionStorage.setItem('token', data.access_token);
            
            // Fetch user info to store role/org
            const user = await this.request('/auth/me');
            sessionStorage.setItem('user_data', JSON.stringify(user));
            return user;
        } catch (e) {
            return false;
        }
    }

    static async deleteSelf(password) {
        return this.request('/auth/me/delete-confirm', {
            method: 'POST',
            body: JSON.stringify({ password })
        });
    }

    static async adminDeleteUser(userId) {
        return this.request(`/org/users/${userId}`, {
            method: 'DELETE'
        });
    }

    // --- Invoices ---
    static async getDashboardStats(userId = null) {
        let url = '/analytics/summary';
        if (userId) url += `?user_id=${userId}`;
        return this.request(url);
    }

    static async getInvoices(skip = 0, limit = 50, search = '', location = '', userId = null) {
        let url = `/invoices?skip=${skip}&limit=${limit}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (location) url += `&location=${encodeURIComponent(location)}`;
        if (userId) url += `&user_id=${userId}`;
        return this.request(url);
    }
    
    static async getInvoice(id) {
        return this.request(`/invoices/${id}`);
    }

    static async createInvoice(data) {
        return this.request('/invoices', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async updateInvoice(id, data) {
        return this.request(`/invoices/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
    
    static async updateInvoiceStatus(id, status) {
        return this.request(`/invoices/${id}/status`, {
            method: 'PATCH',
            body: JSON.stringify({ status })
        });
    }

    static async deleteInvoice(id) {
        return this.request(`/invoices/${id}`, {
            method: 'DELETE'
        });
    }

    static async cloneInvoice(id) {
        return this.request(`/invoices/${id}/clone`, {
            method: 'POST'
        });
    }
    
    // --- PDF ---
    static async downloadPdf(id) {
        const token = this.getToken();
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        
        try {
            const response = await fetch(`${API_BASE}/pdf/${id}`, { headers });
            
            if (!response.ok) {
                let errorMsg = 'PDF Generation Failed';
                try {
                    const data = await response.json();
                    errorMsg = data.error || data.detail || errorMsg;
                } catch (e) {}
                showToast(errorMsg, 'error');
                throw new Error(errorMsg);
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            // Get filename from header if possible, else default
            const disposition = response.headers.get('content-disposition');
            let filename = `invoice-${id}.pdf`;
            if (disposition && disposition.indexOf('filename="') !== -1) {
                filename = disposition.split('filename="')[1].split('"')[0];
            }
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (e) {
            showToast(e.message, 'error');
        }
    }
    
    // --- AI ---
    static async expandDescription(phrase) {
        return this.request('/ai/expand-description', {
            method: 'POST',
            body: JSON.stringify({ phrase })
        });
    }

    static async draftNote(data) {
        return this.request('/ai/draft-note', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async suggestTax(address, items = []) {
        return this.request('/ai/suggest-tax', {
            method: 'POST',
            body: JSON.stringify({ address, items })
        });
    }

    static async auditInvoice(items, currency = 'INR') {
        return this.request('/ai/audit', {
            method: 'POST',
            body: JSON.stringify({ items, currency })
        });
    }

    // --- Email ---
    static async sendInvoiceEmail(invoiceId) {
        return this.request(`/email/send-invoice-email/${invoiceId}`, {
            method: 'POST'
        });
    }

    // --- Profile ---
    static async getProfile() {
        return this.request('/profile/');
    }

    static async updateProfile(data) {
        return this.request('/profile/', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // --- Organization ---
    static async getOrgUsers() {
        return this.request('/org/users');
    }

    static async approveUser(email) {
        return this.request(`/org/approve-user?user_email=${encodeURIComponent(email)}`, {
            method: 'POST'
        });
    }

    static async rejectUser(email) {
        return this.request(`/org/reject-user?user_email=${encodeURIComponent(email)}`, {
            method: 'POST'
        });
    }

    static async toggleUserStatus(userId) {
        return this.request(`/org/toggle-status/${userId}`, {
            method: 'POST'
        });
    }

    // --- Clients ---
    static async getClients() {
        return this.request('/clients/');
    }

    static async getClient(id) {
        return this.request(`/clients/${id}`);
    }

    static async createClient(data) {
        return this.request('/clients/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async updateClient(id, data) {
        return this.request(`/clients/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async deleteClient(id) {
        return this.request(`/clients/${id}`, {
            method: 'DELETE'
        });
    }

    // --- Design Engine ---
    static async analyzeDesign(formData) {
        const token = this.getToken();
        const response = await fetch(`${API_BASE}/design/analyze`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Design analysis failed');
        }
        return await response.json();
    }

    static async getActiveDesign() {
        return this.request('/design/active');
    }

    static async resetDesign() {
        return this.request('/design/reset', { method: 'DELETE' });
    }

    // --- Utils ---
    static async getExchangeRates() {
        return this.request('/utils/rates');
    }
}
