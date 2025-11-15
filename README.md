# PhotoLog Backend API

FastAPI backend for PhotoLog - Event photo sharing platform with Firebase authentication.

## Features

- Firebase Authentication (Email/Password + Google Sign-In)
- Token verification and user management
- Admin authentication
- RESTful API endpoints
- CORS enabled for frontend integration

## Tech Stack

- **FastAPI** - Modern Python web framework
- **Firebase Admin SDK** - Token verification and user management
- **Pydantic** - Data validation and settings management
- **Uvicorn** - ASGI server

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Firebase Configuration

1. You already have `firebase_account_services.json` - make sure it's in the `backend/` directory
2. The file is already in `.gitignore` to keep it secure

### 3. Environment Variables

Create a `.env` file in the `backend/` directory:

```env
FIREBASE_CREDENTIALS_PATH=./firebase_account_services.json
FRONTEND_URL=http://localhost:5173
ADMIN_EMAILS=admin@photolog.com
```

### 4. Run the Server

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the built-in runner
python -m app.main
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## Authentication Flow

### How It Works

1. **Frontend** authenticates users via Firebase (Email/Password or Google Sign-In)
2. **Frontend** receives Firebase ID token after successful authentication
3. **Frontend** sends token to backend in `Authorization: Bearer <token>` header or request body
4. **Backend** verifies token using Firebase Admin SDK
5. **Backend** returns user information

### Supported Auth Methods

- ✅ Email/Password signup and signin
- ✅ Google Sign-In (OAuth)
- ✅ Email verification
- ✅ Password reset
- ✅ Token refresh

**Note**: The backend doesn't distinguish between email/password and Google sign-in - both methods return Firebase ID tokens that are verified the same way.

## API Endpoints

### Authentication (`/auth/*`)

- `POST /auth/signup` - Register new user (requires Firebase token)
- `POST /auth/signin` - User login (requires Firebase token)
- `POST /auth/signout` - Sign out
- `POST /auth/refresh` - Refresh authentication token
- `POST /auth/verify-email` - Verify email address
- `POST /auth/resend-verification` - Resend verification email
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password

### Host Profile (`/me/*`)

- `GET /me` - Get current user profile (protected)
- `PATCH /me` - Update user profile (protected)
- `PATCH /me/password` - Change password (protected)

### Events (`/events/*`)

- `POST /events` - Create a new event
- `GET /events` - List all events for the current host
- `GET /events/{event_id}` - Get details for a specific event
- `PATCH /events/{event_id}` - Update an event's metadata
- `DELETE /events/{event_id}` - Delete an event
- `POST /events/{event_id}/cover` - (Placeholder) Upload a cover image
- `GET /events/{event_id}/qr` - (Placeholder) Get a QR code for the event
- `POST /events/{event_id}/download` - (Placeholder) Trigger a ZIP export of all photos
- `POST /events/actions/bulk` - Perform bulk actions on events

### Photos (Host Moderation) (`/events/{event_id}/photos/*`)

- `GET /events/{event_id}/photos` - Get a paginated list of photos for an event
- `PATCH /events/{event_id}/photos/{photo_id}` - Update photo metadata (caption, approval)
- `DELETE /events/{event_id}/photos/{photo_id}` - Delete a single photo
- `POST /events/{event_id}/photos/bulk-delete` - Delete multiple photos
- `POST /events/{event_id}/photos/bulk-download` - (Placeholder) Trigger a download of selected photos

### Admin Authentication (`/admin/auth/*`)

- `POST /admin/auth/signin` - Admin login
- `POST /admin/auth/signout` - Admin sign out
- `POST /admin/auth/refresh` - Refresh admin token

### Admin Dashboard (`/admin/*`)

- `GET /admin/overview` - Get system-wide statistics
- `GET /admin/events` - List all events in the system
- `GET /admin/events/{event_id}` - Inspect a specific event
- `PATCH /admin/events/{event_id}/status` - Update an event's status
- `DELETE /admin/events/{event_id}` - Force-delete an event
- `GET /admin/uploads/recent` - Get a feed of recent photo uploads
- `GET /admin/users` - List all users
- `GET /admin/users/{user_id}` - Inspect a specific user
- `PATCH /admin/users/{user_id}/status` - Suspend or reactivate a user
- `GET /admin/logs` - (Placeholder) Retrieve audit logs
- `POST /admin/system/export` - (Placeholder) Trigger a system data export

### Utilities

- `GET /health` - Health check endpoint
- `GET /` - API information

## Testing the API

### Using the Interactive Docs

1. Start the server
2. Visit http://localhost:8000/docs
3. Try the `/health` endpoint first
4. For auth endpoints, you'll need a Firebase ID token from your frontend

### Using Postman/Thunder Client

1. Get a Firebase ID token from your frontend after signing in
2. For protected routes, use `Authorization: Bearer <token>` header
3. For signup/signin endpoints, send token in request body: `{"token": "<firebase-token>"}`

### Example Request

```bash
# Health check
curl http://localhost:8000/health

# Signin (requires Firebase token from frontend)
curl -X POST http://localhost:8000/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_FIREBASE_ID_TOKEN"}'

# Get current user (protected route)
curl http://localhost:8000/me \
  -H "Authorization: Bearer YOUR_FIREBASE_ID_TOKEN"
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py             # Configuration and settings
│   ├── dependencies.py       # Auth dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── admin.py         # Admin dashboard models
│   │   ├── auth.py          # Auth request/response models
│   │   ├── event.py         # Event models
│   │   ├── photo.py         # Photo models
│   │   └── user.py          # User models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── admin.py         # Admin dashboard endpoints
│   │   ├── admin_auth.py    # Admin auth endpoints
│   │   ├── auth.py          # Auth endpoints
│   │   ├── events.py        # Event management endpoints
│   │   ├── photos.py        # Photo moderation endpoints
│   │   └── profiles.py      # User profile endpoints
│   └── services/
│       ├── __init__.py
│       └── firebase.py      # Firebase Admin SDK service
├── firebase_account_services.json  # Firebase credentials (keep secret!)
├── requirements.txt
├── .env                      # Environment variables (create this)
└── README.md
```

## Security Notes

- ✅ Firebase credentials file is in `.gitignore`
- ✅ Never commit `firebase_account_services.json` to version control
- ✅ Tokens are verified on every protected route
- ✅ CORS is configured to only allow your frontend domain
- ✅ Admin access is restricted to configured admin emails

## Next Steps

1. **Implement Database Logic**:
   - Integrate a database (e.g., SQLite, PostgreSQL).
   - Replace all mock in-memory databases (`MOCK_DB_*`) with real database queries.
   - Implement full CRUD operations for users, events, and photos.
2. **Implement File Storage**:
   - Integrate a file storage service (e.g., Firebase Storage, AWS S3).
   - Implement photo upload/download logic in the respective endpoints.
3. **Flesh out Placeholder Endpoints**:
   - Implement QR code generation.
   - Implement background tasks for ZIP exports and system data exports.
   - Implement audit logging.

## Troubleshooting

### Firebase credentials not found

Make sure `firebase_account_services.json` is in the `backend/` directory and the path in `.env` is correct.

### Token verification fails

- Check that Firebase Authentication is enabled in Firebase Console
- Verify the token hasn't expired (tokens expire after 1 hour)
- Ensure Email/Password and Google Sign-In providers are enabled in Firebase

### CORS errors

Update `FRONTEND_URL` in `.env` to match your frontend URL.

## License

Private project - All rights reserved

