/**
 * Auth Flow Logic
 * Handles 3-step OTP Authentication.
 */

let isRecoveryMode = false;
let currentEmail = '';
let setupToken = '';
let authMode = 'signin';   // 'signin' or 'signup'
let portalMode = 'admin'; // 'admin' or 'user'

document.addEventListener('DOMContentLoaded', () => {
    setupOtpInputs();
    setupEventListeners();
    switchPortal('admin'); // Default
    switchAuthMode('signin'); // Default
});

function setupOtpInputs() {
    const boxes = document.querySelectorAll('.otp-box');
    boxes.forEach((box, idx) => {
        // Handle typing
        box.addEventListener('input', (e) => {
            if (e.target.value.length === 1 && idx < boxes.length - 1) {
                boxes[idx + 1].focus();
            }
        });

        // Handle backspace
        box.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && !e.target.value && idx > 0) {
                boxes[idx - 1].focus();
            }
        });
    });
}

function setupEventListeners() {
    // Step 1 -> Step 2 (Normal)
    document.getElementById('btn-next-email').addEventListener('click', handleRequestOtp);
    
    // Step 1 -> Step 1.5 (Forgot Password)
    const btnForgot = document.getElementById('btn-forgot-password');
    if (btnForgot) {
        btnForgot.addEventListener('click', () => {
            showStep('step-forgot-password');
        });
    }

    // Step 3 Forgot Password
    const btn3 = document.getElementById('btn-forgot-password-step3');
    if (btn3) btn3.addEventListener('click', handleRecoveryRequest);

    // Step 1.5 -> Step 2 (Recovery)
    document.getElementById('btn-recovery-next').addEventListener('click', handleRecoveryRequest);

    // Back to Login
    document.querySelectorAll('.back-to-login').forEach(btn => {
        btn.addEventListener('click', () => {
            isRecoveryMode = false;
            showStep('step-email');
        });
    });

    // Step 2 -> Step 3
    document.getElementById('btn-verify-otp').addEventListener('click', handleVerifyOtp);
    
    // Portal Toggles
    document.getElementById('portal-admin').addEventListener('click', () => switchPortal('admin'));
    document.getElementById('portal-user').addEventListener('click', () => switchPortal('user'));

    // Auth Mode Toggles
    const btnSignIn = document.getElementById('toggle-signin');
    const btnSignUp = document.getElementById('toggle-signup');

    btnSignIn.addEventListener('click', () => switchAuthMode('signin'));
    btnSignUp.addEventListener('click', () => switchAuthMode('signup'));

    // Step 3 -> Dashboard
    document.getElementById('btn-finish').addEventListener('click', handleFinishSetup);
    
    // Resend
    document.getElementById('btn-resend-otp').addEventListener('click', () => {
        if (isRecoveryMode) handleRecoveryRequest();
        else handleRequestOtp();
    });

    // Password Visibility Toggle
    document.querySelectorAll('.password-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (input.type === 'password') {
                input.type = 'text';
                btn.innerText = 'HIDE';
            } else {
                input.type = 'password';
                btn.innerText = 'SHOW';
            }
        });
    });

    // Back to email from password step
    document.querySelectorAll('.btn-back-to-email').forEach(btn => {
        btn.addEventListener('click', () => {
            showStep('step-email');
        });
    });

    // Escape key global listener
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const passwordStep = document.getElementById('step-password');
            if (passwordStep && passwordStep.style.display === 'block') {
                showStep('step-email');
            }
        }
    });
}

function switchPortal(portal) {
    portalMode = portal;
    const btnAdmin = document.getElementById('portal-admin');
    const btnUser = document.getElementById('portal-user');

    if (portal === 'admin') {
        btnAdmin.classList.add('active');
        btnUser.classList.remove('active');
    } else {
        btnUser.classList.add('active');
        btnAdmin.classList.remove('active');
    }
    
    // Refresh visibility based on portal change
    updateFieldVisibility();
}

function switchAuthMode(mode) {
    authMode = mode;
    const btnSignIn = document.getElementById('toggle-signin');
    const btnSignUp = document.getElementById('toggle-signup');
    const authHint = document.getElementById('auth-hint');
    const nextBtn = document.getElementById('btn-next-email');

    if (mode === 'signup') {
        btnSignUp.classList.add('active');
        btnSignIn.classList.remove('active');
        authHint.innerText = 'New here? Create your organization or join a team.';
        nextBtn.innerText = 'Start Setup';
    } else {
        btnSignIn.classList.add('active');
        btnSignUp.classList.remove('active');
        authHint.innerText = 'Returning user? Sign in to access your invoices.';
        nextBtn.innerText = 'Continue';
    }

    updateFieldVisibility();
}

function updateFieldVisibility() {
    const regContainer = document.getElementById('registration-fields-container');
    const adminFields = document.getElementById('admin-registration-fields');
    const userFields = document.getElementById('user-registration-fields');

    if (authMode === 'signup') {
        regContainer.style.display = 'block';
        if (portalMode === 'admin') {
            adminFields.style.display = 'block';
            userFields.style.display = 'none';
        } else {
            adminFields.style.display = 'none';
            userFields.style.display = 'block';
        }
    } else {
        regContainer.style.display = 'none';
    }
}

async function handleRequestOtp() {
    const emailInput = document.getElementById('email-input');
    currentEmail = emailInput.value.trim();
    
    if (!validateEmail(currentEmail)) {
        showToast('Please enter a valid business email', 'error');
        return;
    }

    const btn = document.getElementById('btn-next-email');
    btn.disabled = true;
    btn.innerText = 'Checking...';

    try {
        const userStatus = await ApiClient.checkUser(currentEmail);
        
        // --- SMART REDIRECT ---
        // If the user exists, we should ALWAYS ask for a password, 
        // even if they accidentally clicked "SIGN UP".
        if (userStatus.exists) {
            if (authMode === 'signup') {
                showToast('Email already registered. Switching to Sign In...', 'info');
                switchAuthMode('signin');
            }
            
            // Show a role-specific badge if they are an admin
            const adminBadge = document.getElementById('admin-badge');
            if (adminBadge) {
                // We hint it if they are in Admin Portal or if the backend can tell us
                // Since checkUser doesn't return role yet, let's use the Portal state as a hint
                adminBadge.style.display = (portalMode === 'admin') ? 'inline-block' : 'none';
            }
            
            window.userExists = true;
            showStep('step-password');
        } else {
            // New user - only allow if in signup mode
            if (authMode === 'signin') {
                showToast('Account not registered. Please sign up.', 'error');
                return;
            }
            
            await ApiClient.requestOtp(currentEmail);
            showToast('Verification code sent!', 'success');
            isRecoveryMode = false;
            document.getElementById('display-email').innerText = currentEmail;
            showStep('step-otp');
            document.querySelector('.otp-box').focus();
        }
    } catch (e) {
        console.error("[AUTH ERROR]", e);
        showToast(`System Error: ${e.message || 'Connection failed'}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerText = 'Continue';
    }
}

async function handleRecoveryRequest() {
    const recoveryInput = document.getElementById('recovery-email-input');
    const emailToRecover = currentEmail || recoveryInput.value.trim();

    if (!validateEmail(emailToRecover)) {
        showToast('Valid email required', 'error');
        return;
    }

    const userStatus = await ApiClient.checkUser(emailToRecover);
    if (!userStatus.exists) {
        showToast('User does not exist', 'error');
        return;
    }

    const btns = [document.getElementById('btn-recovery-next'), document.getElementById('btn-forgot-password-step3')];
    btns.forEach(b => { if(b) b.disabled = true; });

    try {
        await ApiClient.forgotPassword(emailToRecover);
        currentEmail = emailToRecover;
        isRecoveryMode = true;
        
        showToast('Recovery code sent.', 'success');
        document.getElementById('display-email').innerText = emailToRecover;
        showStep('step-otp');
        document.querySelector('.otp-box').focus();
        
    } catch (e) {
        showToast('Recovery failed.', 'error');
    } finally {
        btns.forEach(b => { if(b) b.disabled = false; });
    }
}

async function handleVerifyOtp() {
    const boxes = document.querySelectorAll('.otp-box');
    const otp = Array.from(boxes).map(b => b.value).join('');
    
    if (otp.length < 6) {
        showToast('Enter 6-digit code', 'error');
        return;
    }

    const btn = document.getElementById('btn-verify-otp');
    btn.disabled = true;
    btn.innerText = 'Verifying...';

    try {
        if (isRecoveryMode) {
            window.currentOtp = otp; 
            showStep('step-password');
        } else {
            const response = await ApiClient.verifyOtp(currentEmail, otp);
            setupToken = response.setup_token;
            showStep('step-password');
        }
    } catch (e) {
        const msg = e.detail || e.message || 'Incorrect OTP';
        showToast(msg, 'error');
    } finally {
        btn.disabled = false;
        btn.innerText = 'Verify Code';
    }
}

async function handleFinishSetup() {
    const password = document.getElementById('password-input').value;
    const role = portalMode; // Use the global portal state
    let adminEmail = document.getElementById('admin-email-input').value.trim();
    if (!adminEmail) adminEmail = null;

    if (password.length < 8) {
        showToast('Password: 8+ chars required', 'error');
        return;
    }

    const btn = document.getElementById('btn-finish');
    btn.disabled = true;
    btn.innerText = 'Processing...';

    try {
        if (isRecoveryMode) {
            const data = await ApiClient.resetPassword(currentEmail, window.currentOtp, password);
            if (data) {
                showToast('Password reset successful!', 'success');
                window.location.href = data.role === 'admin' ? '/' : '/create';
            }
        } else if (window.userExists) {
            const data = await ApiClient.login(currentEmail, password, role);
            if (data) {
                showToast('Welcome back!', 'success');
                window.location.href = data.role === 'admin' ? '/' : '/create';
            }
        } else {
            const registrationData = {};
            if (role === 'admin') {
                registrationData.company_name = document.getElementById('company-name-input').value.trim();
                registrationData.gstin = document.getElementById('gstin-input').value.trim();
                registrationData.pan = document.getElementById('pan-input').value.trim();
                registrationData.address = document.getElementById('company-address-input').value.trim();
                
                if (!registrationData.company_name || !registrationData.gstin) {
                    showToast('Company Name and GSTIN required', 'error');
                    btn.disabled = false;
                    btn.innerText = 'Complete Setup';
                    return;
                }
            }

            const data = await ApiClient.setPassword(currentEmail, password, setupToken, role, adminEmail, registrationData);
            if (data && data.access_token) {
                sessionStorage.setItem('user_data', JSON.stringify(data));
                window.location.href = data.role === 'admin' ? '/' : '/create';
            }
        }
    } catch (e) {
        const errorMsg = e.detail || e.message || (typeof e === 'string' ? e : 'An error occurred');
        showToast(errorMsg, 'error');
    } finally {
        btn.disabled = false;
        btn.innerText = isRecoveryMode ? 'Reset Password' : (window.userExists ? 'Sign In' : 'Complete Setup');
    }
}

function showStep(stepId) {
    document.querySelectorAll('.auth-step').forEach(step => {
        step.style.display = 'none';
    });
    const target = document.getElementById(stepId);
    if (target) target.style.display = 'block';

    // Special handling for Step 3 (Password/Setup)
    if (stepId === 'step-password') {
        const loginForgot = document.getElementById('login-forgot-container');
        const finishBtn = document.getElementById('btn-finish');
        const passwordLabel = document.getElementById('password-label');
        const passwordInput = document.getElementById('password-input');

        if (window.userExists) {
            // SIGN IN STATE
            loginForgot.style.display = 'block';
            finishBtn.innerText = 'Sign In';
            passwordLabel.innerText = 'Enter Password';
            passwordInput.placeholder = '••••••••';
        } else {
            // SIGN UP / SETUP STATE
            loginForgot.style.display = 'none';
            finishBtn.innerText = 'Complete Setup';
            passwordLabel.innerText = 'Create Password';
            passwordInput.placeholder = 'Minimum 8 characters';
            passwordInput.value = ''; // Clear password when entering setup
        }

        // Populate summary email
        const summaryEmail = document.getElementById('summary-email');
        if (summaryEmail) summaryEmail.innerText = currentEmail;
    }
}

function validateEmail(email) {
    return String(email)
        .toLowerCase()
        .match(/^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/);
}
