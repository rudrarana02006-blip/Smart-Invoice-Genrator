"""
Email Service — Centralized system for all automated email communications.
Design-aligned with the premium Smart Invoice aesthetic (Black/Orange/Glass).
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from config import settings

async def send_otp_email(email: str, otp: str, subject: str = "Verification Code", body_text: str = "Use the following 6-digit code to complete your session."):
    """Sends a premium monochromatic OTP email."""
    html_template = f"""
    <div style="font-family: 'Inter', sans-serif; background: #000; color: #fff; padding: 40px; max-width: 500px; border: 1px solid #222; border-radius: 12px; margin: 0 auto;">
        <div style="font-family: 'NDot', monospace; font-size: 24px; border-bottom: 1px solid #1a1a1a; padding-bottom: 20px; margin-bottom: 30px; letter-spacing: 2px;">
            SMART INVOICE. <span style="color: #FF5722;">AUTH</span>
        </div>
        
        <h2 style="font-size: 14px; text-transform: uppercase; letter-spacing: 2px; color: #666; margin-bottom: 10px;">Security Verification</h2>
        
        <p style="color: #aaa; font-size: 14px; line-height: 1.6; margin-bottom: 32px;">
            {body_text}
        </p>
        
        <div style="background: #111; padding: 40px; border-radius: 8px; text-align: center; border: 1px solid #222; box-shadow: inset 0 0 20px rgba(255, 87, 34, 0.05);">
            <span style="font-family: 'NDot', monospace; font-size: 42px; letter-spacing: 12px; color: #FF5722; font-weight: bold;">
                {otp}
            </span>
        </div>
        
        <p style="color: #444; font-size: 11px; margin-top: 40px; text-align: center;">
            This code expires in 5 minutes. If you did not request this, please secure your account.
        </p>
        
        <div style="font-size: 9px; color: #222; margin-top: 60px; border-top: 1px solid #111; padding-top: 20px; text-align: center; text-transform: uppercase; letter-spacing: 3px;">
            Smart Invoice inc. — intelligent billing systems
        </div>
    </div>
    """
    return await _send_email_async(email, subject, html_template)

async def send_password_reset_confirmation(email: str, location: str = "Unknown"):
    """Sends a security confirmation after password change."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%d/%m/%Y")
    time_str = now.strftime("%H:%M:%S UTC")
    
    html_template = f"""
    <div style="font-family: 'Inter', sans-serif; background: #000; color: #fff; padding: 40px; max-width: 500px; border: 1px solid #222; border-radius: 12px; margin: 0 auto;">
        <div style="font-family: 'NDot', monospace; font-size: 24px; border-bottom: 1px solid #1a1a1a; padding-bottom: 20px; margin-bottom: 30px; letter-spacing: 2px;">
            SMART INVOICE. <span style="color: #FF5722;">SECURITY</span>
        </div>
        
        <h2 style="font-size: 16px; text-transform: uppercase; letter-spacing: 1px; color: #fff;">Password Updated</h2>
        
        <p style="color: #aaa; font-size: 14px; line-height: 1.6; margin-bottom: 30px;">
            Your account password was successfully changed.
        </p>
        
        <div style="background: #111; padding: 24px; border-radius: 8px; border: 1px solid #222;">
            <table style="width: 100%; font-size: 12px; color: #eee; border-collapse: collapse;">
                <tr><td style="color: #555; padding: 4px 0; width: 100px;">TIME</td><td>{time_str}</td></tr>
                <tr><td style="color: #555; padding: 4px 0;">DATE</td><td>{date_str}</td></tr>
                <tr><td style="color: #555; padding: 4px 0;">LOCATION</td><td>{location}</td></tr>
            </table>
        </div>
        
        <p style="color: #FF5722; font-size: 11px; font-weight: bold; margin-top: 40px; text-align: center; text-transform: uppercase;">
            If this was not you, lock your account immediately.
        </p>
    </div>
    """
    return await _send_email_async(email, "Security Alert: Password Updated", html_template)

async def _send_email_async(to_email: str, subject: str, body_html: str):
    """Core SMTP helper."""
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        print(f"CRITICAL: SMTP credentials missing for {to_email}")
        return False

    msg = MIMEMultipart()
    msg['From'] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_USERNAME}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body_html, 'html'))

    try:
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=10)
        server.starttls()
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        server.sendmail(settings.MAIL_USERNAME, to_email, msg.as_string())
        server.quit()
        print(f"DEBUG: Email successfully sent to {to_email}")
        return True
    except Exception as e:
        print(f"SMTP ERROR for {to_email}: {str(e)}")
        return False
