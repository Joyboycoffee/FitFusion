document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('forgot-password-form');
    const otpSection = document.getElementById('otp-section');
    const sendOtpBtn = document.getElementById('forgot-send-otp');
    const resetBtn = document.getElementById('forgot-reset-password');
    const messageDiv = document.getElementById('forgot-message');

    let email = '';

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        email = document.getElementById('forgot-email').value;
        messageDiv.textContent = '';
        sendOtpBtn.disabled = true;
        try {
            const res = await fetch('/api/request_reset', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email})
            });
            const data = await res.json();
            if (res.ok) {
                otpSection.style.display = '';
                sendOtpBtn.style.display = 'none';
                messageDiv.textContent = 'OTP sent to your email.';
            } else {
                messageDiv.textContent = data.error || 'Failed to send OTP.';
            }
        } catch (err) {
            messageDiv.textContent = 'Network error.';
        }
        sendOtpBtn.disabled = false;
    });

    resetBtn.addEventListener('click', async function() {
        const otp = document.getElementById('forgot-otp').value;
        const newPassword = document.getElementById('forgot-new-password').value;
        messageDiv.textContent = '';
        resetBtn.disabled = true;
        try {
            const res = await fetch('/api/reset_password', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, otp, new_password: newPassword})
            });
            const data = await res.json();
            if (res.ok) {
                messageDiv.textContent = 'Password reset successful. You can now log in.';
                setTimeout(() => { window.location.href = '/'; }, 2000);
            } else {
                messageDiv.textContent = data.error || 'Failed to reset password.';
            }
        } catch (err) {
            messageDiv.textContent = 'Network error.';
        }
        resetBtn.disabled = false;
    });
});
