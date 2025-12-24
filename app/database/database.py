import os
from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
)
from sqlalchemy.orm import sessionmaker, declarative_base
import dotenv

dotenv.load_dotenv()

database_host = os.getenv("POSTGRES_HOST")
database_port = os.getenv("POSTGRES_PORT")
database_user = os.getenv("POSTGRES_USER")
database_password = os.getenv("POSTGRES_PASSWORD")
database_name = os.getenv("POSTGRES_DB")


# 密码 URL 编码（非常重要）
database_password = quote_plus(database_password)

# 异步数据库连接 URL
DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{database_user}:{database_password}"
    f"@{database_host}:{database_port}/{database_name}"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

Base = declarative_base()
