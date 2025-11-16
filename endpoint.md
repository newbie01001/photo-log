## Backend Endpoint Inventory

- **Auth**
  - `POST /auth/signup` – register host; return profile + verification trigger
  - `POST /auth/signin` – host login, issue session/JWT
  - `POST /auth/signout` – invalidate session/token
  - `POST /auth/refresh` – rotate tokens (if using refresh flow)
  - `POST /auth/verify-email` – confirm verification token
  - `POST /auth/resend-verification` – resend email link
  - `POST /auth/forgot-password` – send reset email
  - `POST /auth/reset-password` – confirm reset token + set new password

- **Host Profile**
  - `GET /me` – current host profile + plan/limits (includes avatar URLs)
  - `PATCH /me` – update profile settings (name, contact, avatar URLs)
  - `POST /me/avatar` – upload/replace avatar
  - `PATCH /me/password` – change password (authenticated)

- **Events**
  - `POST /events` – create event (name, description, date, password, cover)
  - `GET /events` – list host’s events with summary stats
  - `GET /events/:eventId` – event detail incl. share links + counts
  - `PATCH /events/:eventId` – update event metadata
  - `DELETE /events/:eventId` – delete event & associated assets
  - `POST /events/:eventId/cover` – upload/replace cover image (stores full image and thumbnail URL, records file size)
  - `GET /events/:eventId/qr` – fetch/generate QR code asset
  - `POST /events/:eventId/download` – trigger ZIP export of photos
  - `POST /events/:eventId/actions` – bulk actions (archive, toggle status, etc.)

- **Photos (Host moderation)**
  - `GET /events/:eventId/photos` – paginated photo list with metadata & status
  - `PATCH /events/:eventId/photos/:photoId` – update caption/approval
  - `DELETE /events/:eventId/photos/:photoId` – remove single photo (from DB and Cloudinary)
  - `POST /events/:eventId/photos/bulk-delete` – delete multiple photos (from DB and Cloudinary)
  - `POST /events/:eventId/photos/bulk-download` – download selected subset

- **Public Visitor Flow**
  - `GET /public/events/:slug` – public event info (name, description, cover, settings)
  - `GET /public/events/:slug/photos` – approved photos (paginated)
  - `POST /public/events/:slug/photos` – upload photo(s); handle optional password & caption (counts towards host's 1GB limit, stores unique public uploader ID)
  - `POST /public/events/:slug/verify-password` – verify event password prior to upload (if used)

- **Admin Auth**
  - `POST /admin/auth/signin`
  - `POST /admin/auth/signout`
  - `POST /admin/auth/refresh` (if needed)

- **Admin Dashboard**
  - `GET /admin/overview` – totals (events, users, photos, storage, includes accurate storage calculation)
  - `GET /admin/events` – list/search/filter all events
  - `GET /admin/events/:eventId` – deep event inspection (photos, host, status)
  - `PATCH /admin/events/:eventId/status` – disable/enable/feature events
  - `DELETE /admin/events/:eventId` – force-delete event (from DB and Cloudinary, including all associated photos and cover image)
  - `GET /admin/uploads/recent` – recent uploads activity feed
  - `GET /admin/users` – host accounts list
  - `GET /admin/users/:userId` – host profile + events
  - `PATCH /admin/users/:userId/status` – suspend/reactivate host
  - `GET /admin/logs` – audit/event logs (if logging to API)
  - `POST /admin/system/export` – export data snapshots

- **Utilities**
  - `GET /health` – basic service health
  - `GET /metrics` – (optional) expose metrics for monitoring
  - `GET /config/public` – deliver public configuration (limits, CDN URLs)

These cover all flows implied by the frontend (host, guest, admin). Adjust naming or combine where needed, but ensure each front-end feature has a matching endpoint.