"""
Configuration management using Pydantic Settings.
Loads environment variables from .env file.
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database configuration
    # Example for PostgreSQL: "postgresql://user:password@host:port/dbname"
    database_url: str = "postgresql://user:password@localhost/photolog"
    
    # Firebase configuration
    # Path to the Firebase service account key file. Can be relative or absolute.
    firebase_credentials_path: str = "firebase_account_services.json"
    
    # Frontend configuration
    frontend_url: str = "http://localhost:5173"
    
    # Admin emails (hardcoded for now, move to database later)
    # Can be set as comma-separated string in .env: ADMIN_EMAILS=admin@photolog.com,admin2@photolog.com
    admin_emails: str = "" # Changed default to empty string for better security
    
    def get_admin_emails_list(self) -> List[str]:
        """
        Parses the comma-separated admin_emails string into a list of email addresses.
        Returns an empty list if no admin emails are configured.
        """
        if not self.admin_emails:
            return []
        return [email.strip() for email in self.admin_emails.split(",") if email.strip()]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_firebase_credentials_path() -> Path:
    """
    Determines the absolute path to the Firebase service account credentials file.
    If `firebase_credentials_path` is relative, it's resolved against the current
    working directory (where the backend server is typically run from).
    """
    cred_path = Path(settings.firebase_credentials_path)
    if not cred_path.is_absolute():
        # Since the server is always run from the backend directory,
        # use the current working directory as the base path
        backend_dir = Path(os.getcwd())
        cred_path = backend_dir / cred_path
    return cred_path.resolve()

