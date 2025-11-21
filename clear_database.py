#!/usr/bin/env python3
"""
Script to clear all data from the database.
WARNING: This will delete ALL users, events, and photos from the database.
Use with caution!
"""
import sys
from app.database import SessionLocal
from app.models.user import User
from app.models.event import Event
from app.models.photo import Photo

def get_counts(db):
    """Get counts of records in each table."""
    photo_count = db.query(Photo).count()
    event_count = db.query(Event).count()
    user_count = db.query(User).count()
    return photo_count, event_count, user_count

def clear_database(confirm=False):
    """
    Clear all data from the database.
    
    Args:
        confirm: If True, skip confirmation prompt (useful for automation)
    """
    db = SessionLocal()
    
    try:
        # Get current counts
        photo_count, event_count, user_count = get_counts(db)
        
        print("=" * 60)
        print("DATABASE CLEAR SCRIPT")
        print("=" * 60)
        print(f"\nCurrent database contents:")
        print(f"  - Photos: {photo_count}")
        print(f"  - Events: {event_count}")
        print(f"  - Users: {user_count}")
        print(f"  - Total records: {photo_count + event_count + user_count}")
        print()
        
        if not confirm:
            response = input("⚠️  WARNING: This will DELETE ALL DATA from the database!\n"
                           "Type 'DELETE ALL' (in uppercase) to confirm: ")
            if response != "DELETE ALL":
                print("❌ Operation cancelled. No data was deleted.")
                return
        
        print("\n🗑️  Starting deletion...")
        
        # Delete in order: Photos -> Events -> Users
        # (Photos have FK to Events, Events have FK to Users)
        
        # Delete all photos
        deleted_photos = db.query(Photo).delete()
        print(f"  ✓ Deleted {deleted_photos} photo(s)")
        
        # Delete all events
        deleted_events = db.query(Event).delete()
        print(f"  ✓ Deleted {deleted_events} event(s)")
        
        # Delete all users
        deleted_users = db.query(User).delete()
        print(f"  ✓ Deleted {deleted_users} user(s)")
        
        # Commit the transaction
        db.commit()
        
        # Verify deletion
        photo_count, event_count, user_count = get_counts(db)
        print()
        print("=" * 60)
        print("✅ Database cleared successfully!")
        print("=" * 60)
        print(f"\nRemaining records:")
        print(f"  - Photos: {photo_count}")
        print(f"  - Events: {event_count}")
        print(f"  - Users: {user_count}")
        print()
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error occurred: {e}")
        print("Transaction rolled back. No data was deleted.")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clear all data from the database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clear_database.py              # Interactive mode (asks for confirmation)
  python clear_database.py --yes       # Skip confirmation (for automation)
        """
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt (use with caution!)"
    )
    
    args = parser.parse_args()
    
    clear_database(confirm=args.yes)

