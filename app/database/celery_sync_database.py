import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import dotenv

dotenv.load_dotenv()

database_host = os.getenv("POSTGRES_HOST")
database_port = os.getenv("POSTGRES_PORT")
database_user = os.getenv("POSTGRES_USER")
database_password = quote_plus(os.getenv("POSTGRES_PASSWORD"))
database_name = os.getenv("POSTGRES_DB")

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{database_user}:{database_password}"
    f"@{database_host}:{database_port}/{database_name}"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()
