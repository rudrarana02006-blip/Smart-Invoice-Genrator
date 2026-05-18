/**
 * Invoice Form Logic — Handles dynamic line items, real-time calculation, and submission.
 */

function setTaxRate(id, rate) {
    const el = document.getElementById(id);
    if (el) {
        el.value = rate;
        calculateTotals();
    }
}

async function handleCountryChange() {
    const country = document.getElementById('client_country').value;
    const profile = await ApiClient.getProfile();
    const orgCountry = (profile.country || 'India').toLowerCase();
    const isDomestic = country.toLowerCase() === orgCountry;

    console.log(`DEBUG: Country Change to ${country}. Org is ${orgCountry}. Domestic: ${isDomestic}`);

    // 1. Auto-Switch Currency
    const currencyMap = {
        'USA': 'USD', 'UK': 'GBP', 'Germany': 'EUR', 'France': 'EUR',
        'Japan': 'JPY', 'UAE': 'AED', 'Canada': 'CAD', 'Australia': 'AUD',
        'Singapore': 'SGD', 'India': 'INR'
    };
    if (currencyMap[country]) {
        document.getElementById('currency').value = currencyMap[country];
    }

    // 2. Trigger Smart Tax Logic (Local Engine)
    handleSuggestTax(null, country);
}

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    setNavUsername();
    
    const user = JSON.parse(sessionStorage.getItem('user_data') || '{}');
    if (user.status === 'pending') {
        document.querySelector('.content-area').innerHTML = `
            <div class="glass-panel" style="text-align: center; padding: 60px; border: 1px solid var(--accent-orange);">
                <div style="font-size: 48px; margin-bottom: 24px; color: var(--accent-orange);">●</div>
                <h2 style="color: var(--text-primary); margin-bottom: 12px;">Account Pending Approval</h2>
                <p style="color: var(--text-secondary); max-width: 400px; margin: 0 auto 32px auto;">
                    Your account is currently waiting for approval from your Organization Admin. 
                    You will be able to create invoices once approved.
                </p>
                <a href="/" class="btn btn-secondary">Return to Dashboard</a>
            </div>
        `;
        return;
    }

    initForm();
    setupEventListeners();
});

let activeDesign = 'classic';
let lineItemCount = 0;
let globalRates = null; // Store fetched exchange rates
let availableBanks = [];
let orgCountry = 'India';

function initForm() {
    // Add first empty row
    addLineItem();
    
    // Set default tax rates (9+9 = 18% standard)
    document.getElementById('cgst_rate').value = 9;
    document.getElementById('sgst_rate').value = 9;

    // Set default due date to 30 days from now
    const dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + 30);
    document.getElementById('due_date').valueAsDate = dueDate;
    
    // Load Bank Accounts
    loadBankAccounts();
}

async function loadBankAccounts() {
    try {
        const profile = await ApiClient.getProfile();
        availableBanks = profile.bank_accounts || [];
        orgCountry = profile.country || 'India';
        console.log("DEBUG: Organization Country detected as:", orgCountry);
        
        const select = document.getElementById('bank_select');
        if (!select) return;
        select.innerHTML = '<option value="">Default Bank Account</option>';
        availableBanks.forEach((bank, idx) => {
            const opt = document.createElement('option');
            opt.value = idx;
            opt.textContent = `${bank.bank_name} - ${bank.account_no}`;
            select.appendChild(opt);
        });
    } catch(e) {
        console.error('Failed to load banks', e);
    }
}

function setupEventListeners() {
    // Subtotal listeners
    document.getElementById('cgst_rate').addEventListener('input', calculateTotals);
    document.getElementById('sgst_rate').addEventListener('input', calculateTotals);
    document.getElementById('currency').addEventListener('change', calculateTotals);
    
    // Suggest Tax Button
    const btnSuggestTax = document.getElementById('btnSuggestTax');
    if (btnSuggestTax) {
        btnSuggestTax.addEventListener('click', (e) => handleSuggestTax(e, null, true));
    }

    // Add item button
    document.getElementById('btnAddItem').addEventListener('click', addLineItem);
    
    // Client Country auto-config
    document.getElementById('client_country').addEventListener('change', handleCountryChange);
    
    // Template Toggle
    const chkTemplate = document.getElementById('is_template');
    if (chkTemplate) {
        chkTemplate.addEventListener('change', (e) => {
            document.getElementById('recurrence_group').style.display = e.target.checked ? 'block' : 'none';
        });
    }

    // AI Audit Button
    const btnAudit = document.getElementById('btnAudit');
    if (btnAudit) {
        btnAudit.addEventListener('click', handleAudit);
    }

    // Live Currency Conversion
    document.getElementById('currency').addEventListener('change', handleCurrencyChangeWithFX);

    // Note generator
    document.getElementById('btnDraftNote').addEventListener('click', handleDraftNote);

    // Form Submission
    const form = document.getElementById('invoiceForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    // Check for prefill data (from Client Management page)
    const prefill = sessionStorage.getItem('prefill_client');
    if (prefill) {
        try {
            const client = JSON.parse(prefill);
            document.getElementById('client_name').value = client.name || '';
            document.getElementById('client_email').value = client.email || '';
            document.getElementById('client_address').value = client.address || '';
            // Clear it so it doesn't stick for next time
            sessionStorage.removeItem('prefill_client');
        } catch (e) {
            console.error("Prefill error:", e);
        }
    }

    const btnSaveDraft = document.getElementById('btnSaveDraft');
    if (btnSaveDraft) {
        btnSaveDraft.addEventListener('click', (e) => {
            window._forceStatus = 'draft';
            handleFormSubmit(e);
        });
    }
}

/**
 * Live Currency Conversion Logic
 */
async function handleCurrencyChangeWithFX() {
    const currency = document.getElementById('currency').value;
    
    // Fetch rates if not already available
    if (!globalRates) {
        try {
            const data = await ApiClient.getExchangeRates();
            globalRates = data.rates;
            // Base is INR (1.0)
            globalRates['INR'] = 1.0;
        } catch (e) {
            console.error("Failed to fetch rates:", e);
            return; // Fallback to normal calculateTotals
        }
    }

    const previousCurrency = document.getElementById('currency').dataset.prev || 'INR';
    const rateFrom = globalRates[previousCurrency];
    const rateTo = globalRates[currency];

    if (rateFrom && rateTo) {
        const factor = rateTo / rateFrom;
        
        // Update all line item rates
        document.querySelectorAll('.item-rate').forEach(input => {
            const currentVal = parseFloat(input.value) || 0;
            input.value = (currentVal * factor).toFixed(2);
        });
    }

    document.getElementById('currency').dataset.prev = currency;
    calculateTotals();
}

/**
 * AI Audit Logic
 */
async function handleAudit() {
    const items = [];
    document.querySelectorAll('.line-item-row').forEach(row => {
        items.push({
            description: row.querySelector('.item-desc').value,
            quantity: parseFloat(row.querySelector('.item-qty').value) || 0,
            rate: parseFloat(row.querySelector('.item-rate').value) || 0
        });
    });

    if (items.length === 0) {
        showToast("Add some items first", "warning");
        return;
    }

    const btn = document.getElementById('btnAudit');
    const originalText = btn.innerText;
    btn.innerText = "Auditing...";
    btn.disabled = true;

    try {
        const currency = document.getElementById('currency').value;
        const result = await ApiClient.auditInvoice(items, currency);
        
        const panel = document.getElementById('audit_results');
        const badge = document.getElementById('audit_status_badge');
        const note = document.getElementById('audit_note');
        const issuesList = document.getElementById('audit_issues');

        panel.style.display = 'block';
        note.innerText = result.audit_note;
        issuesList.innerHTML = '';

        if (result.is_safe) {
            badge.innerText = "SAFE";
            badge.className = "badge badge-success";
        } else {
            badge.innerText = "FLAGGED";
            badge.className = "badge badge-warning";
            result.issues.forEach(issue => {
                const li = document.createElement('li');
                li.innerText = issue;
                issuesList.appendChild(li);
            });
        }
    } catch (e) {
        console.error(e);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

function addLineItem() {
    lineItemCount++;
    const id = `item_${lineItemCount}`;
    
    const row = document.createElement('div');
    row.className = 'line-item-row';
    row.id = id;
    
    row.innerHTML = `
        <div class="form-group" style="position: relative;">
            <input type="text" class="form-control item-desc" placeholder="Item description" required>
            <a href="#" class="btn-ai-expand" style="position: absolute; right: 8px; top: 50%; transform: translateY(-50%); font-size: 10px; color: var(--accent-orange); text-decoration: none; display: none;">(AI)</a>
        </div>
        <div class="form-group">
            <input type="number" class="form-control item-qty" placeholder="0" min="0.001" step="0.001" required>
        </div>
        <div class="form-group">
            <input type="text" class="form-control item-unit" placeholder="Unit" value="Nos">
        </div>
        <div class="form-group">
            <input type="number" class="form-control item-rate" placeholder="0.00" min="0" step="0.01" required>
        </div>
        <div class="line-amount" id="amount_${id}">0.00</div>
        <button type="button" class="btn-remove" onclick="removeLineItem('${id}')">✕</button>
    `;
    
    document.getElementById('lineItemsContainer').appendChild(row);
    
    // Show AI button on input
    const descInput = row.querySelector('.item-desc');
    const aiBtn = row.querySelector('.btn-ai-expand');
    
    // Real-time Unit Intelligence
    descInput.addEventListener('input', debounce((e) => {
        const val = e.target.value.toLowerCase();
        const unitInput = row.querySelector('.item-unit');
        
        // --- UNIVERSAL UNIT DICTIONARY ---
        // 1. PRECIOUS METALS
        if (val.includes('gold') || val.includes('silver') || val.includes('jewel') || val.includes('diamond') || val.includes('pearl')) {
            unitInput.value = 'Grams';
        } 
        // 2. LOGISTICS & TRANSPORT
        else if (val.includes('freight') || val.includes('transport') || val.includes('logistics') || val.includes('delivery') || val.includes('courier') || val.includes('shipping')) {
            unitInput.value = 'Trips';
        }
        else if (val.includes('fuel') || val.includes('petrol') || val.includes('diesel')) {
            unitInput.value = 'Liters';
        }
        // 3. MANUFACTURING & RAW MATERIALS
        else if (val.includes('steel') || val.includes('iron') || val.includes('cement') || val.includes('sand') || val.includes('scrap') || val.includes('chemical')) {
            unitInput.value = 'Tons';
        }
        else if (val.includes('weight') || val.includes('load') || val.includes('cargo') || val.includes('grain') || val.includes('food')) {
            unitInput.value = 'Kgs';
        }
        // 4. PROFESSIONAL SERVICES
        else if (val.includes('service') || val.includes('consult') || val.includes('it ') || val.includes('software') || val.includes('dev') || val.includes('design') || val.includes('legal') || val.includes('audit')) {
            unitInput.value = 'Hours';
        }
        else if (val.includes('session') || val.includes('training') || val.includes('class') || val.includes('visit')) {
            unitInput.value = 'Sessions';
        }
        // 5. TEXTILES & MATERIALS
        else if (val.includes('fabric') || val.includes('cloth') || val.includes('wire') || val.includes('cable') || val.includes('pipe')) {
            unitInput.value = 'Meters';
        }
        // 6. REAL ESTATE & SPACE
        else if (val.includes('land') || val.includes('area') || val.includes('flat') || val.includes('office') || val.includes('shop') || val.includes('plot')) {
            unitInput.value = 'Sq. Ft.';
        }
        // 7. SUBSCRIPTIONS & TIME
        else if (val.includes('subscription') || val.includes('license') || val.includes('rent') || val.includes('lease')) {
            unitInput.value = 'Months';
        }
        // 8. RETAIL & GENERAL
        else if (val.includes('pack') || val.includes('box') || val.includes('carton') || val.includes('set')) {
            unitInput.value = 'Packs';
        }
        else {
            unitInput.value = 'Nos';
        }
        
        // Trigger Tax Suggestion if it's the first time
        if (val.length > 3) handleSuggestTax(null, null, false);
    }, 500));
    
    // Expand description button
    aiBtn.addEventListener('click', (e) => {
        e.preventDefault();
        expandDescription(descInput);
    });

    descInput.addEventListener('input', () => {
        aiBtn.style.display = descInput.value.trim().length > 2 ? 'block' : 'none';
    });
    
    aiBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        if (aiBtn.disabled) return;
        
        const phrase = descInput.value.trim();
        console.log("DEBUG: AI Expand Triggered. Phrase:", phrase);
        if (!phrase) return;
        
        const originalVal = descInput.value;
        const originalText = aiBtn.textContent;
        
        aiBtn.disabled = true;
        aiBtn.textContent = '...';
        descInput.disabled = true;
        
        try {
            const response = await ApiClient.expandDescription(phrase);
            console.log("DEBUG: AI Expander Response:", response);
            descInput.value = response.suggestion || response.expanded_description;
        } catch (e) {
            console.error("AI Expander Error:", e);
            descInput.value = originalVal;
            if (e.message && (e.message.includes("busy") || e.message.includes("Quota"))) {
                showToast('AI Quota Limit Reached', 'error', 30);
                disableAIButtons(30);
            } else {
                showToast(e.message || 'AI expansion failed', 'error');
            }
        } finally {
            descInput.disabled = false;
            aiBtn.textContent = '✔️';
            aiBtn.style.color = '#34c759';
            setTimeout(() => {
                aiBtn.textContent = originalText;
                aiBtn.style.color = 'var(--accent-orange)';
                aiBtn.disabled = false;
            }, 2000);
        }
    });
    
    // Add input listeners for calculation
    row.querySelector('.item-qty').addEventListener('input', calculateTotals);
    row.querySelector('.item-rate').addEventListener('input', calculateTotals);
}

function removeLineItem(id) {
    const row = document.getElementById(id);
    if (row) {
        row.remove();
        calculateTotals();
    }
}

function calculateTotals() {
    const currencySelect = document.getElementById('currency');
    const currency = currencySelect.value;
    const symbols = {
        'INR': '₹', 'USD': '$', 'EUR': '€', 'GBP': '£',
        'JPY': '¥', 'AED': 'د.إ', 'CAD': '$', 'AUD': '$', 'SGD': '$'
    };
    const symbol = symbols[currency] || '$';
    let subtotal = 0;
    
    // Calculate line items
    document.querySelectorAll('.line-item-row').forEach(row => {
        const qty = parseFloat(row.querySelector('.item-qty').value) || 0;
        const rate = parseFloat(row.querySelector('.item-rate').value) || 0;
        const amount = qty * rate;
        
        row.querySelector('.line-amount').textContent = `${symbol} ${amount.toFixed(2)}`;
        subtotal += amount;
    });
    
    // Calculate Taxes
    const cgstRate = parseFloat(document.getElementById('cgst_rate').value) || 0;
    const sgstRate = parseFloat(document.getElementById('sgst_rate').value) || 0;
    
    const tax1Amount = subtotal * (cgstRate / 100);
    const tax2Amount = subtotal * (sgstRate / 100);
    
    const total = subtotal + tax1Amount + tax2Amount;
    
    // Set Summary Values
    document.getElementById('summary_subtotal').innerText = subtotal.toFixed(2);
    document.getElementById('summary_cgst').innerText = tax1Amount.toFixed(2);
    document.getElementById('summary_sgst').innerText = tax2Amount.toFixed(2);
    document.getElementById('summary_total').innerText = total.toFixed(2);
}

async function handleSuggestTax(e, overrideAddress = null, forceAI = false) {
    if (e) e.preventDefault();
    const btn = document.getElementById('btnSuggestTax');
    if (btn && btn.disabled) return;
    
    const address = overrideAddress || document.getElementById('client_address').value.trim();
    const items = [];
    document.querySelectorAll('.item-desc').forEach(input => {
        if (input.value.trim()) items.push(input.value.trim());
    });

    if (!address && items.length === 0) {
        showToast('Please enter an address or select a country', 'error');
        return;
    }
    
    const originalText = btn ? btn.textContent : 'AI SUGGEST';
    if (btn) {
        btn.textContent = '...';
        btn.disabled = true;
    }

    const orgCountryLower = orgCountry.toLowerCase();
    const addressLower = address.toLowerCase();
    const clientCountry = document.getElementById('client_country').value.toLowerCase();
    const isDomestic = clientCountry === orgCountryLower || addressLower.includes(orgCountryLower);

    try {
        let result = null;

        // 1. LOCAL ENGINE (Fast heuristics)
        if (!forceAI) {
            if (orgCountryLower === 'india') {
                const itemsLower = items.join(' ').toLowerCase();
                
                if (isDomestic) {
                    const txt = itemsLower;
                    // 1. PRECIOUS METALS (3%)
                    if (txt.includes('gold') || txt.includes('silver') || txt.includes('jewelry') || txt.includes('jewellery') || txt.includes('diamond') || txt.includes('pearl')) {
                        result = { tax_1_name: 'CGST', tax_1_rate: 1.5, tax_2_name: 'SGST', tax_2_rate: 1.5 };
                    }
                    // 2. ESSENTIALS & AGRI (5%)
                    else if (txt.includes('grain') || txt.includes('sugar') || txt.includes('spices') || txt.includes('tea') || txt.includes('coffee') || txt.includes('oil') || txt.includes('fertilizer') || txt.includes('cotton')) {
                        result = { tax_1_name: 'CGST', tax_1_rate: 2.5, tax_2_name: 'SGST', tax_2_rate: 2.5 };
                    }
                    // 3. PROCESSED FOOD & HOUSEHOLD (12%)
                    else if (txt.includes('fruit juice') || txt.includes('cheese') || txt.includes('ghee') || txt.includes('dry fruit') || txt.includes('cell phone') || txt.includes('ketchup')) {
                        result = { tax_1_name: 'CGST', tax_1_rate: 6.0, tax_2_name: 'SGST', tax_2_rate: 6.0 };
                    }
                    // 4. STANDARD SERVICES & ELECTRONICS (18%)
                    else if (txt.includes('it') || txt.includes('software') || txt.includes('consulting') || txt.includes('laptop') || txt.includes('monitor') || txt.includes('camera') || txt.includes('service') || txt.includes('advertising') || txt.includes('rent')) {
                        result = { tax_1_name: 'CGST', tax_1_rate: 9.0, tax_2_name: 'SGST', tax_2_rate: 9.0 };
                    }
                    // 5. LUXURY & SIN (28%)
                    else if (txt.includes('ac ') || txt.includes('air conditioner') || txt.includes('refrigerator') || txt.includes('washing machine') || txt.includes('car') || txt.includes('automobile') || txt.includes('luxury') || txt.includes('tobacco') || txt.includes('cement')) {
                        result = { tax_1_name: 'CGST', tax_1_rate: 14.0, tax_2_name: 'SGST', tax_2_rate: 14.0 };
                    }
                    // 6. DEFAULT (18% - Most common for B2B)
                    else {
                        result = { tax_1_name: 'CGST', tax_1_rate: 9.0, tax_2_name: 'SGST', tax_2_rate: 9.0 };
                    }
                } else if (address.length >= 2 || clientCountry) {
                    result = { tax_1_name: 'Export (Zero Rated GST)', tax_1_rate: 0, tax_2_name: '', tax_2_rate: 0 };
                }
            }
        }

        // 2. AI ENGINE (Deep analysis if local fails or forced)
        if (!result) {
            console.log("DEBUG: Calling AI for tax suggestion...");
            result = await ApiClient.suggestTax(address, items);
        }

        // Apply Result
        if (result) {
            applyTaxResult(result);
            showToast(forceAI ? 'AI Suggested Slabs' : 'Tax Configured');
        }

    } catch (err) {
        console.error("Tax Engine Error:", err);
        showToast('AI analysis failed. Using defaults.', 'error');
    } finally {
        if (btn) {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }
}

function applyTaxResult(result) {
    if (!result) return;

    // Tax 1
    const t1Label = document.getElementById('label_tax_1');
    const t1SumLabel = document.getElementById('label_summary_tax_1');
    const t1Input = document.getElementById('cgst_rate');
    
    if (t1Label) t1Label.innerText = `${result.tax_1_name} Rate (%)`;
    if (t1SumLabel) t1SumLabel.innerText = result.tax_1_name;
    if (t1Input) t1Input.value = result.tax_1_rate;

    // Tax 2
    const t2Row = document.getElementById('row_summary_tax_2');
    const t2Label = document.getElementById('label_tax_2');
    const t2SumLabel = document.getElementById('label_summary_tax_2');
    const t2Input = document.getElementById('sgst_rate');

    if (result.tax_2_name) {
        if (t2Label) t2Label.innerText = `${result.tax_2_name} Rate (%)`;
        if (t2SumLabel) t2SumLabel.innerText = result.tax_2_name;
        if (t2Input) {
            t2Input.value = result.tax_2_rate;
            t2Input.closest('.form-group').style.display = 'block';
        }
        if (t2Row) t2Row.style.display = 'flex';
    } else {
        if (t2Row) t2Row.style.display = 'none';
        if (t2Input) {
            t2Input.closest('.form-group').style.display = 'none';
            t2Input.value = 0;
        }
    }

    calculateTotals();
}

async function handleDraftNote(e) {
    const btn = e.target;
    if (btn.disabled) return;

    const clientName = document.getElementById('client_name').value.trim();
    const totalText = document.getElementById('summary_total').textContent;
    const total = parseFloat(totalText.replace(/[^0-9.]/g, '')) || 0;
    
    if (!clientName) {
        showToast('Please enter client name', 'error');
        return;
    }
    
    const originalText = btn.textContent;
    btn.textContent = '...';
    btn.disabled = true;
    
    try {
        const currency = document.getElementById('currency').value;
        const response = await ApiClient.draftNote({
            client_name: clientName,
            total_amount: total,
            currency: currency
        });
        let note = response.suggestion || response.note;
        if (currency === 'INR') note = note.replace(/\$/g, '₹');
        
        document.getElementById('notes').value = note;
        showToast('Note drafted!');
    } catch (e) {
        console.error("AI Note Error:", e);
        if (e.message && (e.message.includes("busy") || e.message.includes("Quota"))) {
            showToast('AI Quota Limit Reached', 'error', 30);
            disableAIButtons(30);
        } else {
            showToast(e.message || 'Note drafting failed', 'error');
        }
    } finally {
        btn.textContent = 'DRAFTED';
        btn.style.color = '#34c759';
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.color = '';
            btn.disabled = false;
        }, 2000);
    }
}

function disableAIButtons(seconds) {
    const buttons = [
        document.getElementById('btnDraftNote'),
        document.getElementById('btnSuggestTax'),
        ...document.querySelectorAll('.btn-ai-expand')
    ];
    
    buttons.forEach(btn => {
        if (!btn) return;
        btn.disabled = true;
        btn.style.opacity = '0.5';
    });
    
    setTimeout(() => {
        buttons.forEach(btn => {
            if (!btn) return;
            btn.disabled = false;
            btn.style.opacity = '1';
        });
    }, seconds * 1000);
}

async function handleFormSubmit(e) {
    e.preventDefault();
    console.log("DEBUG: handleFormSubmit started");
    
    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn ? btn.textContent : 'Create Invoice';
    
    try {
        if (btn) {
            btn.textContent = 'Preparing...';
            btn.disabled = true;
        }

        const items = [];
        document.querySelectorAll('.line-item-row').forEach(row => {
            const desc = row.querySelector('.item-desc').value;
            if (desc && desc.trim()) {
                items.push({
                    description: desc.trim(),
                    quantity: parseFloat(row.querySelector('.item-qty').value) || 0,
                    unit: row.querySelector('.item-unit').value || "Units",
                    rate: parseFloat(row.querySelector('.item-rate').value) || 0
                });
            }
        });
        
        console.log(`DEBUG: Processed ${items.length} items`);

        if (items.length === 0) {
            throw new Error('Please add at least one line item with a description.');
        }
        
        const bankSelect = document.getElementById('bank_select');
        const selectedBankIdx = bankSelect ? bankSelect.value : "";
        const bankId = selectedBankIdx !== "" ? (availableBanks[selectedBankIdx]?.id || null) : null;

        let dueDateVal = document.getElementById('due_date').value;
        if (!dueDateVal) {
            throw new Error('Please select a due date.');
        }

        const specificNumber = document.getElementById('invoice_number').value.trim();
        const prefix = document.getElementById('invoice_number_prefix').value.trim() || 'INV-';
        
        const payload = {
            invoice_number: specificNumber ? (prefix + specificNumber) : "",
            client_name: document.getElementById('client_name').value,
            client_email: document.getElementById('client_email').value,
            client_address: document.getElementById('client_address').value,
            client_country: document.getElementById('client_country').value,
            due_date: new Date(dueDateVal).toISOString(),
            currency: document.getElementById('currency').value || 'INR',
            cgst_rate: parseFloat(document.getElementById('cgst_rate').value) || 0,
            sgst_rate: parseFloat(document.getElementById('sgst_rate').value) || 0,
            items: items,
            notes: document.getElementById('notes').value.trim(),
            status: window._forceStatus || 'sent',
            selected_bank: bankId ? { id: bankId } : null,
            is_template: document.getElementById('is_template')?.checked || false,
            recurrence: document.getElementById('recurrence')?.value || 'none',
            invoice_number_prefix: prefix
        };
        
        if (btn) btn.textContent = 'Creating...';
        
        console.log("DEBUG: Sending to API:", payload);
        const response = await ApiClient.createInvoice(payload);
        console.log("DEBUG: API Response:", response);
        
        showToast('Invoice created successfully!');
        setTimeout(() => window.location.href = '/invoices', 1000);

    } catch (err) {
        console.error("DEBUG: Submission failed:", err);
        showToast(err.message || 'Submission failed', 'error');
        
        if (btn) {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }
}
