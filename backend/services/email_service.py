import smtplib
import os
from email.message import EmailMessage

# Pull credentials from your .env file
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.mailtrap.io")
SMTP_PORT = int(os.getenv("SMTP_PORT", "2525"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

def send_action_email(to_email: str, subject: str, body: str, from_email: str, lead_id: str):
    """
    Sends an email using standard SMTP.
    Appends a basic opt-out link.
    Returns True if successful, False otherwise.
    """
    if not to_email:
        print(f"Failed to send: No email address provided for lead {lead_id}")
        return False

    opt_out_url = f"http://localhost:3000/opt-out/{lead_id}"
    
    full_body = f"{body}\n\n--\nTo opt out of future messages, please visit: {opt_out_url}"

    msg = EmailMessage()
    msg.set_content(full_body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        
        # Only start TLS and login if credentials exist
        if SMTP_USER and SMTP_PASS:
            server.starttls() 
            server.login(SMTP_USER, SMTP_PASS)
            
        server.send_message(msg)
        server.quit()
        print(f"Successfully sent email to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}. Error: {str(e)}")
        return False