"""
Email service for sending notifications.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional
import logging
from jinja2 import Template

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self):
        self.enabled = settings.email_enabled
        self.from_email = settings.email_from
        self.from_name = settings.email_from_name
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
    
    def _load_template(self, template_name: str) -> Template:
        """Load email template from file."""
        template_path = Path(__file__).parent.parent / "templates" / "emails" / template_name
        if not template_path.exists():
            logger.warning(f"Template {template_name} not found, using default")
            return Template("{{ content }}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return Template(f.read())
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email via SMTP."""
        if not self.enabled or not self.smtp_password:
            logger.warning("Email service is disabled or not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add content
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_welcome_email(self, user_email: str, user_name: Optional[str] = None) -> bool:
        """Send welcome email to new user."""
        template = self._load_template("welcome.html")
        html_content = template.render(
            user_name=user_name or "there",
            app_name="PHOTO LOG",
            frontend_url=settings.frontend_url
        )
        
        subject = "Welcome to PHOTO LOG!"
        return self._send_email(user_email, subject, html_content)
    
    def send_photo_approved_email(
        self,
        user_email: str,
        event_name: str,
        photo_url: Optional[str] = None,
        user_name: Optional[str] = None
    ) -> bool:
        """Send email when photo is approved."""
        template = self._load_template("photo_approved.html")
        html_content = template.render(
            user_name=user_name or "there",
            event_name=event_name,
            photo_url=photo_url,
            app_name="PHOTO LOG",
            frontend_url=settings.frontend_url
        )
        
        subject = f"Your photo from '{event_name}' has been approved!"
        return self._send_email(user_email, subject, html_content)
    
    def send_photo_rejected_email(
        self,
        user_email: str,
        event_name: str,
        reason: Optional[str] = None,
        user_name: Optional[str] = None
    ) -> bool:
        """Send email when photo is rejected."""
        template = self._load_template("photo_rejected.html")
        html_content = template.render(
            user_name=user_name or "there",
            event_name=event_name,
            reason=reason or "does not meet our guidelines",
            app_name="PHOTO LOG",
            frontend_url=settings.frontend_url
        )
        
        subject = f"Photo from '{event_name}' needs attention"
        return self._send_email(user_email, subject, html_content)
    
    def send_export_ready_email(
        self,
        user_email: str,
        event_name: str,
        download_link: str,
        photo_count: int,
        user_name: Optional[str] = None
    ) -> bool:
        """Send email when export is ready."""
        template = self._load_template("export_ready.html")
        html_content = template.render(
            user_name=user_name or "there",
            event_name=event_name,
            download_link=download_link,
            photo_count=photo_count,
            app_name="PHOTO LOG"
        )
        
        subject = f"Your photo export from '{event_name}' is ready!"
        return self._send_email(user_email, subject, html_content)


# Global email service instance
email_service = EmailService()

