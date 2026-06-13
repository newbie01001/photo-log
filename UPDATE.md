# Email Service Fix — Update Notes

**Date:** June 2025  
**File changed:** `app/services/email.py`  
**Config change:** `.env` (`SMTP_PORT`)

---

## Problem

Welcome emails (and all other notification emails) were not sending. Signup still worked, but users never received the welcome email.

### Symptoms

- `test_email.py` returned `Result: False`
- Server logs showed one of:
  - `[WinError 10060] A connection attempt failed...` (connection timeout)
  - `535 BadCredentials` (after port fix — invalid/expired Gmail App Password)

### Root causes

1. **Port 587 blocked** — The original code always connected to Gmail on port 587 with STARTTLS. On the dev machine and many hosted servers, outbound port 587 is blocked or unreachable. Connection timed out before login could even happen.
2. **Gmail App Password format** — Google displays App Passwords with spaces (e.g. `abcd efgh ilkl mpop`). Spaces in `.env` could cause auth failures if not handled.
3. **Hosted environment** — Same port 587 issue likely affected production. Many cloud hosts block outbound SMTP on 587 (and sometimes 25) to prevent spam.
4. **Silent failure** — Email is sent in a background task on `/auth/signup`. Failures only appear in logs; the API still returns success.

Templates (`app/templates/emails/`) and email logic were **not** broken — the issue was SMTP connectivity and configuration.

---

## What changed

### 1. `app/services/email.py`

**Before:** Always used port 587 with STARTTLS.

```python
with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
    server.starttls()
    server.login(self.smtp_username, self.smtp_password)
    server.send_message(msg)
```

**After:**

| Change | Details |
|--------|---------|
| New `_connect_smtp()` method | Port **465** → `SMTP_SSL` (implicit SSL). Port **587** → `SMTP` + `starttls()`. |
| 30-second timeout | Avoids hanging indefinitely on blocked ports. |
| `smtp_tls` setting respected | `config.py` already had `smtp_tls`; the original code ignored it. |
| App Password spaces stripped | `settings.smtp_password.replace(" ", "")` so Gmail passwords paste correctly from `.env`. |

### 2. `.env` configuration

```env
# Before (blocked on dev + likely on host)
SMTP_PORT=587

# After (works on dev; try on host)
SMTP_PORT=465
```

Full required email vars:

```env
EMAIL_ENABLED=true
EMAIL_FROM=officialphotolab2025@gmail.com
EMAIL_FROM_NAME=PHOTO LOG
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
SMTP_USERNAME=officialphotolab2025@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_TLS=true
FRONTEND_URL=http://localhost:5173
```

For Gmail, `SMTP_PASSWORD` must be a **Gmail App Password** (Google Account → Security → 2-Step Verification → App passwords), not the regular account password. Spaces in the password are fine in `.env`.

---

## What did NOT change

- Email HTML templates (`welcome.html`, `photo_approved.html`, etc.)
- `send_welcome_email()` and other send methods
- Trigger: welcome email still only fires on `POST /auth/signup` (not signin)
- `app/config.py` defaults (README still documents 587; use 465 where 587 is blocked)

---

## How to test locally

1. Create venv and install deps:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Configure `.env` (see above). Use `SMTP_PORT=465`.

3. Run `test_email.py` from project root:
   ```powershell
   python test_email.py
   ```

4. Expected: `Result: True` and welcome email in inbox (check spam).

### Optional: check which ports work

```python
import socket
for port in (587, 465):
    try:
        socket.create_connection(("smtp.gmail.com", port), timeout=10)
        print(f"port {port}: OK")
    except OSError as e:
        print(f"port {port}: BLOCKED - {e}")
```

---

## Deploying to hosted environment

1. **Set production env vars** — Same as `.env`, especially:
   - `SMTP_PORT=465`
   - `SMTP_PASSWORD` (Gmail App Password)
   - `EMAIL_ENABLED=true`

2. **Deploy updated `email.py`** — The code must include `_connect_smtp()` and SSL support for port 465.

3. **Restart the server** after env changes.

4. **Check server logs** on signup for:
   - `Email sent successfully to ...` (success)
   - Connection timeout (port still blocked — try 465 or a transactional email provider)
   - `535 BadCredentials` (regenerate App Password)

5. **If both 587 and 465 are blocked** on the host, Gmail SMTP will not work from that server. Use a transactional provider (SendGrid, Mailgun, Resend, etc.) and update `email.py` to use their SMTP relay or API.

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `WinError 10060` / timeout | Port 587 blocked | Set `SMTP_PORT=465`, deploy updated `email.py` |
| `535 BadCredentials` | Wrong/expired App Password | Regenerate App Password; ensure `SMTP_USERNAME` matches the Google account |
| `Email service is disabled or not configured` | Missing password or `EMAIL_ENABLED=false` | Set `SMTP_PASSWORD` and `EMAIL_ENABLED=true` in env |
| Signup works, no email | Background task failed | Check server logs; verify env on host, not just local `.env` |
| No email on Google sign-in | Welcome only on `/auth/signup` | Expected unless signin flow is updated to send welcome for new users |

---

## Summary

| Item | Before | After |
|------|--------|-------|
| SMTP connection | Port 587 + STARTTLS only | Port 465 SSL or 587 STARTTLS via `_connect_smtp()` |
| App Password | Used as-is | Spaces stripped automatically |
| `smtp_tls` config | Ignored | Used for non-465 ports |
| Local `.env` | `SMTP_PORT=587` | `SMTP_PORT=465` |
| Templates / send methods | Unchanged | Unchanged |

The fix addresses blocked port 587 on local and hosted networks. After deploying `email.py` and setting `SMTP_PORT=465` (plus a valid Gmail App Password) in production, welcome emails should send on signup.
