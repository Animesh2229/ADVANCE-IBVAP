import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from passlib.context import CryptContext
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.models import Base, User

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://ibvap:ibvap@localhost/ibvap")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                email="admin@ibvap.local",
                hashed_password=pwd_context.hash("Admin@123"),
                full_name="System Administrator",
                role="admin"
            )
            db.add(admin)
            await db.commit()
            print("Admin user created → username: admin | password: Admin@123")
        else:
            print("Admin already exists")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_admin())
