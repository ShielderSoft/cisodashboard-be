"""
Script to reset a user's password
"""
import sys
import asyncio
from app.db.session import SessionLocal
from app.crud.crud_user import user_crud


async def reset_password(email: str, new_password: str):
    """Reset password for a user"""
    async with SessionLocal() as db:
        try:
            user = await user_crud.get_by_email(db, email=email)
            if not user:
                print(f"❌ User not found: {email}")
                return False
            
            await user_crud.update(db, db_obj=user, obj_in={'password': new_password})
            print(f"✅ Password updated successfully for: {email}")
            print(f"   Username: {user.username}")
            print(f"   You can now log in with the new password.")
            return True
            
        except Exception as e:
            print(f"❌ Error resetting password: {str(e)}")
            raise


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python reset_password.py user@example.com newPassword123")
        print("\nExample:")
        print("  python reset_password.py admin@risktrix.com MyNewPassword123")
        sys.exit(1)
    
    email = sys.argv[1]
    new_pw = sys.argv[2]
    
    print(f"\n🔐 Resetting password for: {email}")
    asyncio.run(reset_password(email, new_pw))
