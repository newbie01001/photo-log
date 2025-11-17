# PhotoLog Backend API

FastAPI backend for PhotoLog - Event photo sharing platform with Firebase authentication.

## Features

- Firebase Authentication (Email/Password + Google Sign-In)
- Token verification and user management
- Admin authentication
- Email notifications (Welcome, Photo Approval, Export Ready)
- Public visitor flow for event photo sharing
- User profile pictures (avatars)
- 1GB upload limit per authenticated user (host/admin)
- QR code generation for event sharing
- RESTful API endpoints
- CORS enabled for frontend integration

## Tech Stack

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Robust relational database
- **SQLAlchemy** - Python SQL Toolkit and Object Relational Mapper
- **Alembic** - Database migrations tool
- **Cloudinary** - Cloud-based image and video management
- **Firebase Admin SDK** - Token verification and user management
- **Pydantic** - Data validation and settings management
- **Uvicorn** - ASGI server
- **Jinja2** - Email template rendering
- **qrcode** - QR code generation for event sharing

## Setup Instructions

### 1. Install Dependencies

```bash
# Make sure you are in the 'backend' directory
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
# Also install pydantic[email] for email validation
pip install 'pydantic[email]'
```

### 2. Firebase Configuration

1. You already have `firebase_account_services.json` - make sure it's in the `backend/` directory
2. The file is already in `.gitignore` to keep it secure

### 3. PostgreSQL Database Setup (using Docker)

To run the PostgreSQL database locally for development:

1.  **Install Docker:** If you don't have Docker installed, download and install it from [https://www.docker.com/get-started](https://www.docker.com/get-started).
2.  **Run PostgreSQL Container:** Open your terminal in the `backend/` directory and run:
    ```bash
    docker run --name photolog-db -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d postgres
    ```
    This command starts a PostgreSQL container named `photolog-db` with a default user `postgres` and password `mysecretpassword`, mapping port 5432.

### 4. Environment Variables

Create a `.env` file in the `backend/` directory with the following content:

```env
FIREBASE_CREDENTIALS_PATH=./firebase_account_services.json
FRONTEND_URL=http://localhost:5173
ADMIN_EMAILS=admin@photolog.com
DATABASE_URL=postgresql://postgres:mysecretpassword@localhost:5432/postgres

# Cloudinary URL for image storage
CLOUDINARY_URL="cloudinary://<api_key>:<api_secret>@<cloud_name>"

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
- For email notifications, you need a Gmail App Password. See [EMAIL_SETUP.md](./EMAIL_SETUP.md) for setup instructions.

### 5. Run Database Migrations (Alembic)

After setting up the database and `.env` file, apply the initial database schema:

```bash
# Make sure your virtual environment is activated
alembic upgrade head
```

### 6. Run the Server

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
5. **Backend** creates/retrieves user in **PostgreSQL database** and returns user information

### Supported Auth Methods

- ✅ Email/Password signup and signin
- ✅ Google Sign-In (OAuth)
- ✅ Email verification
- ✅ Password reset (link-based via Firebase)
- ✅ Token refresh

**Note**: The backend doesn't distinguish between email/password and Google sign-in - both methods return Firebase ID tokens that are verified the same way.

**Password Reset**: Uses Firebase's built-in password reset flow. Firebase sends a reset link to the user's email. The backend verifies the token after the password is reset.

## API Endpoints

### Authentication (`/auth/*`)

- `POST /auth/signup` - Register new user (requires Firebase token, **creates user in DB**)
- `POST /auth/signin` - User login (requires Firebase token, **ensures user exists in DB**)
- `POST /auth/signout` - Sign out
- `POST /auth/refresh` - Refresh authentication token
- `POST /auth/verify-email` - Verify email address
- `POST /auth/resend-verification` - Resend verification email
- `POST /auth/forgot-password` - Request password reset (Firebase sends reset link via email)
- `POST /auth/reset-password` - Confirm password reset (after user resets via Firebase link)

### Host Profile (`/me/*`)

- `GET /me` - Get current user profile (**from DB**, protected, includes avatar URLs)
- `PATCH /me` - Update user profile (**in DB**, protected, can update name and avatar URLs)
- `POST /me/avatar` - Upload or replace user's avatar (**to Cloudinary**, protected)
- `PATCH /me/password` - Change password (protected)

### Events (`/events/*`)

- `POST /events` - Create a new event (**in DB**)
- `GET /events` - List all events for the current host (**from DB**)
- `GET /events/{event_id}` - Get details for a specific event (**from DB**)
- `PATCH /events/{event_id}` - Update an event's metadata (**in DB**)
- `DELETE /events/{event_id}` - Delete an event (**from DB**)
- `POST /events/{event_id}/cover` - Upload a cover image (stores full image and thumbnail URL, records file size)
- `GET /events/{event_id}/qr` - Generate QR code for event sharing
- `POST /events/{event_id}/download` - (Placeholder) Trigger a ZIP export of all photos
- `POST /events/actions/bulk` - Perform bulk actions on events (**in DB**)

### Photos (Host Moderation) (`/events/{event_id}/photos/*`)

- `GET /events/{event_id}/photos` - Get a paginated list of photos for an event (**from DB**)
- `PATCH /events/{event_id}/photos/{photo_id}` - Update photo metadata (caption, approval) (**in DB**)
- `DELETE /events/{event_id}/photos/{photo_id}` - Delete a single photo (**from DB and Cloudinary**)
- `POST /events/{event_id}/photos/bulk-delete` - Delete multiple photos (**from DB and Cloudinary**)
- `POST /events/{event_id}/photos/bulk-download` - (Placeholder) Trigger a download of selected photos

### Public Visitor Flow (`/public/*`)

- `GET /public/events/{slug}` - Get public event information
- `GET /public/events/{slug}/photos` - Get approved photos for public viewing (paginated)
- `POST /public/events/{slug}/verify-password` - Verify event password
- `POST /public/events/{slug}/photos` - Upload a photo to a public event (counts towards host's 1GB limit, stores unique public uploader ID)

### Admin Authentication (`/admin/auth/*`)

- `POST /admin/auth/signin` - Admin login
- `POST /admin/auth/signout` - Admin sign out
- `POST /admin/auth/refresh` - Refresh admin token

### Admin Dashboard (`/admin/*`)

- `GET /admin/overview` - Get system-wide statistics (**from DB**, includes accurate storage calculation)
- `GET /admin/events` - List all events in the system (**from DB**)
- `GET /admin/events/{event_id}` - Inspect a specific event (**from DB**)
- `PATCH /admin/events/{event_id}/status` - Update an event's status (**in DB**)
- `DELETE /admin/events/{event_id}` - Force-delete an event (**from DB and Cloudinary, including all associated photos and cover image**)
- `GET /admin/uploads/recent` - Get a feed of recent photo uploads (**from DB**)
- `GET /admin/users` - List all users (**from DB**)
- `GET /admin/users/{user_id}` - Inspect a specific user (**from DB**)
- `PATCH /admin/users/{user_id}/status` - Suspend or reactivate a user (**in DB**)
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
│   ├── database.py           # SQLAlchemy engine, session, and Base
│   ├── dependencies.py       # Auth dependencies
│   ├── crud.py               # CRUD operations for database models
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
│       ├── cloudinary.py    # Cloudinary image upload service
│       ├── firebase.py      # Firebase Admin SDK service
│       └── email.py         # Email notification service
│   └── templates/
│       └── emails/          # Email HTML templates
│           ├── welcome.html
│           ├── photo_approved.html
│           ├── photo_rejected.html
│           └── export_ready.html
├── alembic/                  # Alembic migration scripts
│   ├── versions/
│   └── env.py
├── alembic.ini               # Alembic configuration
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

## Email Notifications

The backend supports email notifications via Gmail SMTP:

- ✅**Welcome emails** - Sent automatically when users sign up
- ✅**Photo approval notifications** - Sent when photos are approved/rejected
- ✅**Export completion notifications** - Ready for use when export feature is implemented

See [EMAIL_SETUP.md](./EMAIL_SETUP.md) for detailed setup instructions.

## Next Steps

1. **Flesh out Placeholder Endpoints**:
   - Implement background tasks for ZIP exports and system data exports.
   - Implement audit log retrieval from a logging service or database.
2. **Enhancements**:
   - Add search and filtering to admin dashboard
   - Implement event slug system (currently uses event ID)
   - Add rate limiting for API endpoints

## Completed

- **File Storage & Management**:
  - Integrated Cloudinary for photo, event cover, and user avatar uploads.
  - Implemented automatic thumbnail generation for event covers and user avatars.
  - Ensured Cloudinary asset deletion upon corresponding database record removal (photos, event covers, user avatars).
  - Added file size tracking for all uploaded assets.
- **Upload Limits**:
  - Implemented a 1GB upload limit per authenticated user (hosts/admins), encompassing all their direct uploads and public uploads to their events.
- **User Avatars**:
  - Added functionality for users to upload and manage their profile pictures (avatars).
- **Data Consistency**:
  - Updated database schemas and Pydantic models to reflect all new fields and functionalities.
  - Applied necessary Alembic migrations.
- **Documentation**:
  - Updated `README.md` to reflect all new features and changes.

## Troubleshooting

### Firebase credentials not found

Make sure `firebase_account_services.json` is in the `backend/` directory and the path in `.env` is correct.

### Token verification fails

- Check that Firebase Authentication is enabled in Firebase Console
- Verify the token hasn't expired (tokens expire after 1 hour)
- Ensure Email/Password and Google Sign-In providers are enabled in Firebase

### CORS errors

Update `FRONTEND_URL` in `.env` to match your frontend URL.

### Email not sending

- Check that `SMTP_PASSWORD` is set correctly (Gmail App Password, not regular password)
- Verify `EMAIL_ENABLED=true` in `.env`
- Ensure 2-Step Verification is enabled on your Google account
- See [EMAIL_SETUP.md](./EMAIL_SETUP.md) for troubleshooting

## License

Private project - All rights reserved

