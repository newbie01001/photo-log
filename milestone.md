# Quick Start Guide

## ✅ What's Been Implemented

Your Firebase Authentication backend with FastAPI is now complete! Here's what's ready:

### ✅ Completed Features

1. **PostgreSQL Database Integration**
   - ✅ SQLAlchemy ORM for models (User, Event, Photo)
   - ✅ Alembic for database migrations
   - ✅ Database session management (`app/database.py`)
   - ✅ Centralized CRUD operations (`app/crud.py`)

2. **Firebase Admin SDK Integration**
   - ✅ Token verification service
   - ✅ Automatic initialization on startup
   - ✅ Error handling for expired/invalid tokens

3. **Authentication Endpoints** (`/auth/*`)
   - ✅ Signup (email/password + Google, **creates user in DB**)
   - ✅ Signin (email/password + Google, **ensures user exists in DB**)
   - ✅ Signout
   - ✅ Token refresh
   - ✅ Email verification
   - ✅ Resend verification
   - ✅ Forgot password (Firebase sends reset link via email)
   - ✅ Reset password (link-based via Firebase)

4. **Host Profile Endpoints** (`/me/*`)
   - ✅ Get current user profile (**from DB**)
   - ✅ Update profile (**in DB**)
   - ✅ Change password

5. **Event Management Endpoints** (`/events/*`) - *Fully Database Integrated*
   - ✅ Create event (**in DB**)
   - ✅ List host's events (**from DB**)
   - ✅ Get event details (**from DB**)
   - ✅ Update event metadata (**in DB**)
   - ✅ Delete event (**from DB**)
   - ✅ (Placeholder) Upload/replace cover image
   - ✅ Generate QR code for event sharing
   - ✅ (Placeholder) Trigger ZIP export of photos
   - ✅ Bulk actions on events (**in DB**)
   - ✅ Share link generation

6. **Photo Moderation Endpoints** (`/events/{event_id}/photos/*`) - *Fully Database Integrated*
   - ✅ Get paginated photo list (**from DB**)
   - ✅ Update photo metadata (caption/approval) (**in DB**)
   - ✅ Remove single photo (**from DB**)
   - ✅ Bulk delete photos (**from DB**)
   - ✅ (Placeholder) Bulk download photos

7. **Admin Dashboard Endpoints** (`/admin/*`) - *Fully Database Integrated*
   - ✅ Get overview stats (**from DB**)
   - ✅ List/search/filter all events (**from DB**)
   - ✅ Deep event inspection (**from DB**)
   - ✅ Update event status (**in DB**)
   - ✅ Force-delete event (**from DB**)
   - ✅ Get recent uploads activity feed (**from DB**)
   - ✅ List host accounts (**from DB**)
   - ✅ Inspect host profile + events (**from DB**)
   - ✅ Suspend/reactivate host (**in DB**)
   - ✅ (Placeholder) Retrieve audit/event logs
   - ✅ (Placeholder) Export data snapshots

8. **Admin Authentication** (`/admin/auth/*`)
   - ✅ Admin signin
   - ✅ Admin signout
   - ✅ Admin token refresh

9. **Configuration**
   - ✅ Environment variables support
   - ✅ Firebase credentials path configured
   - ✅ CORS enabled for frontend
   - ✅ Admin email list configured

10. **Google Sign-In Support**
    - ✅ Works out of the box (no special handling needed)
    - ✅ Same token format as email/password
    - ✅ Same verification process

11. **Email Notifications**
    - ✅ Welcome emails on user signup
    - ✅ Photo approval/rejection notifications
    - ✅ Export ready notifications (ready for integration)
    - ✅ Gmail SMTP integration
    - ✅ HTML email templates

12. **Public Visitor Flow**
    - ✅ Public event viewing (no authentication required)
    - ✅ Public photo viewing (approved photos only)
    - ✅ Password-protected event access
    - ✅ Public photo uploads

13. **QR Code Generation**
    - ✅ QR code generation for event share links
    - ✅ Configurable QR code size
    - ✅ Returns PNG image format

## 🚀 How to Run

### 1. Activate Virtual Environment

```bash
cd backend
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux
```

### 2. Install Dependencies (if not already done)

```bash
pip install -r requirements.txt
# Also install pydantic[email] for email validation
pip install 'pydantic[email]'
```

### 3. Create `.env` File

Create `backend/.env` with:

```env
FIREBASE_CREDENTIALS_PATH=./firebase_account_services.json
FRONTEND_URL=http://localhost:5173
ADMIN_EMAILS=officialphotolab2025@gmail.com
DATABASE_URL=postgresql://postgres:mysecretpassword@localhost:5432/postgres

# Email Configuration (Gmail SMTP)
EMAIL_ENABLED=true
EMAIL_FROM=officialphotolab2025@gmail.com
EMAIL_FROM_NAME=PHOTO LOG
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=officialphotolab2025@gmail.com
SMTP_PASSWORD=your_gmail_app_password_here
SMTP_TLS=true
```
**Important:** 
- Ensure the `DATABASE_URL` matches the credentials used when starting your Docker container.
- For email notifications, see [EMAIL_SETUP.md](./EMAIL_SETUP.md) for Gmail App Password setup.

### 4. PostgreSQL Database Setup (using Docker)

To run the PostgreSQL database locally for development:

1.  **Install Docker:** If you don't have Docker installed, download and install it from [https://www.docker.com/get-started](https://www.docker.com/get-started).
2.  **Run PostgreSQL Container:** Open your terminal in the `backend/` directory and run:
    ```bash
    docker run --name photolog-db -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d postgres
    ```
    This command starts a PostgreSQL container named `photolog-db` with a default user `postgres` and password `mysecretpassword`, mapping port 5432.

### 5. Run Database Migrations (Alembic)

After setting up the database and `.env` file, apply the initial database schema:

```bash
# Make sure your virtual environment is activated
alembic upgrade head
```

### 6. Start the Server

```bash
# Option 1: Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Using Python module
python -m app.main
```

### 7. Test the API

Visit http://localhost:8000/docs to see the interactive API documentation.

Try the health check:
```bash
curl http://localhost:8000/health
```

## 📝 Next Steps

### For Frontend Integration

1. **Install Firebase SDK in Frontend**:
   ```bash
   cd ..  # Go back to frontend directory
   npm install firebase
   ```

2. **Initialize Firebase in Frontend**:
   - Create `src/utils/firebase.js` or similar
   - Add your Firebase config from Firebase Console
   - Initialize Firebase app and auth

3. **Update Signup/Signin Pages**:
   - Add Firebase authentication calls
   - Send Firebase ID token to backend endpoints
   - Store token for authenticated requests

4. **Add API Client**:
   - Create `src/utils/api.js` or similar
   - Add functions to call backend endpoints
   - Include token in Authorization header for protected routes

### For Backend Development

1. **Implement File Storage**:
   - Integrate a file storage service (e.g., Firebase Storage, AWS S3).
   - Implement actual photo and cover image upload/download logic in the respective endpoints.

2. **Flesh out Placeholder Endpoints**:
   - Implement background tasks for ZIP exports of photos and system data exports.
   - Implement audit log retrieval from a logging service or database.

3. **Enhancements**:
   - Add search and filtering to admin dashboard
   - Implement event slug system (currently uses event ID)
   - Add rate limiting for API endpoints

## 🔍 Testing Your Setup

### 1. Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "PhotoLog API"
}
```

### 2. Test with Firebase Token

You'll need a Firebase ID token from your frontend. Once you have it:

```bash
# Signin endpoint
curl -X POST http://localhost:8000/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_FIREBASE_TOKEN"}'
```

### 3. Test Protected Route

```bash
# Get current user (requires token in header)
curl http://localhost:8000/me \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

## 📚 Documentation

- **README.md** - Full documentation
- **GOOGLE_SIGNIN.md** - Google sign-in integration guide
- **endpoint.md** - Complete API endpoint reference

## ⚠️ Important Notes

1. **Firebase Credentials**: `firebase_account_services.json` is in `.gitignore` - keep it secret!

2. **Environment Variables**: Create `.env` file (not committed to git)

3. **Google Sign-In**: Works automatically - no backend changes needed. Just enable it in Firebase Console.

4. **Token Expiration**: Firebase tokens expire after 1 hour. Use `/auth/refresh` to get new tokens.

5. **Admin Access**: Currently checks email against `ADMIN_EMAILS` in config. Will move to database later.

## 🐛 Troubleshooting

### Firebase credentials not found
- Check that `firebase_account_services.json` is in `backend/` directory
- Verify path in `.env` matches actual filename

### Import errors
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

### CORS errors
- Update `FRONTEND_URL` in `.env` to match your frontend URL
- Check that CORS middleware is configured in `app/main.py`

### Token verification fails
- Verify Firebase Authentication is enabled in Firebase Console
- Check that Email/Password and Google providers are enabled
- Ensure token hasn't expired (tokens expire after 1 hour)

## 🎉 You're Ready!

Your backend is fully set up and ready to handle authentication. Start the server and begin integrating with your frontend!

