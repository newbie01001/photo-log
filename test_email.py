import logging
from app.services.email import email_service
from app.config import settings

logging.basicConfig(level=logging.INFO)

TO = "richardtommyandrew@gmail.com"  # change this

print("Config:")
print("  enabled:", settings.email_enabled)
print("  from:", settings.email_from)
print("  smtp:", settings.smtp_server, settings.smtp_port)
print("  password set:", bool(settings.smtp_password))
print("  frontend_url:", settings.frontend_url)
print()

if not settings.email_enabled or not settings.smtp_password:
    print("Fix .env first (EMAIL_ENABLED + SMTP_PASSWORD)")
    raise SystemExit(1)

print("Sending welcome email (template + SMTP)...")
ok = email_service.send_welcome_email(
    user_email=TO,
    user_name="Test User",
)
print("Result:", ok)