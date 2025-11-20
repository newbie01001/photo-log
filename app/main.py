"""
FastAPI application entry point.
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import settings
from app.services.firebase import initialize_firebase
from app.routers import auth, admin_auth, photos, profiles, events, admin, public

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PhotoLog API",
    description="Backend API for PhotoLog - Event photo sharing platform",
    version="1.0.0"
)

# Initialize Firebase Admin SDK on startup
@app.on_event("startup")
async def startup_event():
    """Initialize Firebase Admin SDK when application starts."""
    try:
        initialize_firebase()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://photo-log-ashy.vercel.app",
        "http://localhost:5173",
        "https://photo-log.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin_auth.router)
app.include_router(profiles.router)
app.include_router(photos.router)
app.include_router(events.router)
app.include_router(admin.router)
app.include_router(public.router)



# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic service health check."""
    return {
        "status": "healthy",
        "service": "PhotoLog API"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "PhotoLog API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
        "detail": exc.detail,
        "status_code": exc.status_code
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


