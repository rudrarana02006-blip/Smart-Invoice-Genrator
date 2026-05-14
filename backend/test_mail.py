import os
import smtplib
from dotenv import load_dotenv

# 1. Environment Check
load_dotenv()

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_PORT = os.getenv("MAIL_PORT", "587")
MAIL_SERVER = "smtp.gmail.com"

print("--- SMTP DIAGNOSTIC START ---")
print(f"Username: {MAIL_USERNAME}")
if MAIL_PASSWORD:
    masked_pw = MAIL_PASSWORD[:2] + "*" * (len(MAIL_PASSWORD) - 4) + MAIL_PASSWORD[-2:]
    print(f"Password: {masked_pw} (Length: {len(MAIL_PASSWORD)})")
else:
    print("Password: NOT FOUND IN .ENV")
print(f"Port: {MAIL_PORT}")
print("----------------------------")

# 2. Connection Test
try:
    print(f"Connecting to {MAIL_SERVER}:{MAIL_PORT}...")
    server = smtplib.SMTP(MAIL_SERVER, int(MAIL_PORT), timeout=10)
    server.set_debuglevel(1)
    
    print("Sending STARTTLS...")
    server.starttls()
    
    print(f"Attempting login for {MAIL_USERNAME}...")
    server.login(MAIL_USERNAME, MAIL_PASSWORD)
    
    print("\nSUCCESS: SMTP Connection and Login were successful!")
    server.quit()

# 3. Verbose Error Reporting
except smtplib.SMTPAuthenticationError:
    print("\nERROR: Invalid App Password. Check 2FA and Google App Passwords.")
    print("Make sure you are using a 16-character code, not your main password.")
except (TimeoutError, ConnectionRefusedError):
    print("\nERROR: Connection Blocked. Your network (University Wi-Fi) is likely blocking Port 587.")
    print("Try switching to Port 465 (requires SMTP_SSL) or use a different network.")
except Exception as e:
    print(f"\nRAW ERROR FROM SERVER: {type(e).__name__}: {e}")

print("--- DIAGNOSTIC END ---")
