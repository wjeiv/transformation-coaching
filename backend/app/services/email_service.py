import aiosmtplib
import email.message
from typing import Optional

from app.core.config import settings


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: Optional[str] = None,
) -> bool:
    """Send an email using SMTP."""
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        print("SMTP credentials not configured - skipping email send")
        return False

    try:
        message = email.message.EmailMessage()
        message["From"] = from_email or settings.EMAIL_FROM
        message["To"] = to_email
        message["Subject"] = subject
        
        # Set both HTML and plain text versions
        message.add_alternative(html_body, subtype="html")
        
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            start_tls=True,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


async def send_contact_notification(
    name: str,
    email: str,
    phone: str,
    message: str,
) -> bool:
    """Send notification email for new contact form submission."""
    subject = f"New Contact Form Submission from {name}"
    
    html_body = f"""
    <html>
    <body>
        <h2>New Contact Form Submission</h2>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Phone:</strong> {phone or 'Not provided'}</p>
        <p><strong>Message:</strong></p>
        <p>{message}</p>
        <hr>
        <p><em>This message was sent from the Transformation Coaching contact form.</em></p>
    </body>
    </html>
    """
    
    return await send_email(
        to_email=settings.CONTACT_EMAIL_TO,
        subject=subject,
        html_body=html_body,
    )
