# Quick Start Guide

## ✅ What's Been Implemented

Your Firebase Authentication backend with FastAPI is now complete! Here's what's ready:

### ✅ Completed Features

1. **Firebase Admin SDK Integration**
   - Token verification service
   - Automatic initialization on startup
   - Error handling for expired/invalid tokens

2. **Authentication Endpoints** (`/auth/*`)
   - ✅ Signup (email/password + Google)
   - ✅ Signin (email/password + Google)
   - ✅ Signout
   - ✅ Token refresh
   - ✅ Email verification
   - ✅ Resend verification
   - ✅ Forgot password
   - ✅ Reset password

3. **Host Profile Endpoints** (`/me/*`)
   - ✅ Get current user profile (`/me`)
   - ✅ Update profile (`/me`)
   - ✅ Change password (`/me/password`)

4. **Admin Authentication** (`/admin/auth/*`)
   - ✅ Admin signin
   - ✅ Admin signout
   - ✅ Admin token refresh

5. **Event Management Endpoints** (`/events/*`) - *Initial Placeholder Implementation*
   - ✅ Create event
   - ✅ List host's events
   - ✅ Get event details
   - ✅ Update event metadata
   - ✅ Delete event
   - ✅ (Placeholder) Upload/replace cover image
   - ✅ (Placeholder) Fetch/generate QR code
   - ✅ (Placeholder) Trigger ZIP export of photos
   - ✅ Bulk actions on events

6. **Photo Moderation Endpoints** (`/events/{event_id}/photos/*`) - *Initial Placeholder Implementation*
   - ✅ Get paginated photo list
   - ✅ Update photo metadata (caption/approval)
   - ✅ Remove single photo
   - ✅ Bulk delete photos
   - ✅ (Placeholder) Bulk download photos

7. **Admin Dashboard Endpoints** (`/admin/*`) - *Initial Placeholder Implementation*
   - ✅ Get overview stats
   - ✅ List/search/filter all events
   - ✅ Deep event inspection
   - ✅ Update event status
   - ✅ Force-delete event
   - ✅ Get recent uploads activity feed
   - ✅ List host accounts
   - ✅ Inspect host profile + events
   - ✅ Suspend/reactivate host
   - ✅ (Placeholder) Retrieve audit/event logs
   - ✅ (Placeholder) Export data snapshots

8. **Configuration**
   - ✅ Environment variables support
   - ✅ Firebase credentials path configured
   - ✅ CORS enabled for frontend
   - ✅ Admin email list configured

9. **Google Sign-In Support**
   - ✅ Works out of the box (no special handling needed)
   - ✅ Same token format as email/password
   - ✅ Same verification process

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
```

### 3. Create `.env` File

Create `backend/.env` with:

```env
FIREBASE_CREDENTIALS_PATH=./firebase_account_services.json
FRONTEND_URL=http://localhost:5173
ADMIN_EMAILS=admin@photolog.com
```

### 4. Start the Server

```bash
# Option 1: Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Using Python module
python -m app.main
```

### 5. Test the API

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

1. **Implement Database Integration**:
   - Choose a database (e.g., SQLite, PostgreSQL).
   - Replace all mock in-memory databases (`MOCK_DB_EVENTS`, `MOCK_DB_PHOTOS`, `MOCK_DB_USERS`) with real database queries and ORM (e.g., SQLAlchemy, Tortoise ORM).
   - Implement full CRUD operations for users, events, and photos, persisting data.

2. **Implement File Storage**:
   - Integrate a file storage service (e.g., Firebase Storage, AWS S3).
   - Implement actual photo and cover image upload/download logic in the respective endpoints.

3. **Flesh out Placeholder Endpoints**:
   - Implement actual QR code generation for event share links.
   - Implement background tasks for ZIP exports of photos and system data exports.
   - Implement audit log retrieval from a logging service or database.

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

