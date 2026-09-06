import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from passlib.context import CryptContext

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.models import Base, User

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://ibvap:ibvap@localhost/ibvap")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@ibvap.local")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == ADMIN_USERNAME))
        if not result.scalar_one_or_none():
            admin = User(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                hashed_password=pwd_context.hash(ADMIN_PASSWORD),
                full_name="System Administrator",
                role="admin",
                must_change_password=True,
            )
            db.add(admin)
            await db.commit()
            print(f"Admin user created → username: {ADMIN_USERNAME}")
            print("IMPORTANT: Change the default password immediately in production!")
        else:
            print("Admin already exists")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_admin())
