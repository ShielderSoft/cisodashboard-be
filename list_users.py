"""
Script to list all users in the database with their basic information
"""
import asyncio
from app.db.session import SessionLocal
from sqlalchemy import select
from app.models.models import User


async def list_all_users():
    """List all users from the database"""
    async with SessionLocal() as db:
        try:
            result = await db.execute(select(User).order_by(User.id))
            users = result.scalars().all()
            
            if not users:
                print("No users found in database.")
                return
            
            print(f"\n{'='*80}")
            print(f"Found {len(users)} user(s) in database:")
            print(f"{'='*80}\n")
            
            for user in users:
                print(f"ID: {user.id}")
                print(f"Email: {user.email}")
                print(f"Username: {user.username}")
                print(f"Full Name: {user.full_name}")
                print(f"Role: {user.role}")
                print(f"Active: {user.is_active}")
                print(f"Superuser: {user.is_superuser}")
                print(f"Last Login: {user.last_login}")
                print("-" * 80)
            
            print(f"\n{'='*80}")
            print("Note: Passwords are hashed and cannot be retrieved.")
            print("Use reset_password.py to set a new password for any user.")
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"Error listing users: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(list_all_users())
