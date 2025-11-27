"""
Script to create test users for the application.
Run this once to create a regular user and a creator user.
"""
from database import SessionLocal
from routers.auth import get_password_hash
import models

def create_test_users():
    db = SessionLocal()
    try:
        # Create regular user
        regular_user = db.query(models.User).filter(models.User.username == "testuser").first()
        if not regular_user:
            regular_user = models.User(
                email="testuser@example.com",
                username="testuser",
                hashed_password=get_password_hash("testpass123"),
                role="user"
            )
            db.add(regular_user)
            print("✓ Created regular user: testuser / testpass123")
        else:
            print("✗ Regular user 'testuser' already exists")
        
        # Create creator user
        creator_user = db.query(models.User).filter(models.User.username == "creator").first()
        if not creator_user:
            creator_user = models.User(
                email="creator@example.com",
                username="creator",
                hashed_password=get_password_hash("creator123"),
                role="creator"
            )
            db.add(creator_user)
            print("✓ Created creator user: creator / creator123")
        else:
            print("✗ Creator user 'creator' already exists")
        
        db.commit()
        print("\nTest users created successfully!")
        print("\nCredentials:")
        print("=" * 50)
        print("Regular User:")
        print("  Username: testuser")
        print("  Password: testpass123")
        print("  Role: user")
        print("\nCreator User:")
        print("  Username: creator")
        print("  Password: creator123")
        print("  Role: creator")
        print("=" * 50)
        
    except Exception as e:
        db.rollback()
        print(f"Error creating users: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()

