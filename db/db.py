# db/db.py
import os
import sys
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("MYSQL_URL")  # expected SQLAlchemy URL for MySQL
engine = None

def _make_engine(url: str):
    return create_engine(url, future=True, echo=False)

if DATABASE_URL:
    try:
        engine = _make_engine(DATABASE_URL)
        # quick smoke test: try to connect once
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("Using MySQL DB from MYSQL_URL")
    except Exception as e:
        print("WARNING: Could not connect to MYSQL_URL. Falling back to local SQLite. Error:")
        traceback.print_exc(limit=5)
        DATABASE_URL = None

if not DATABASE_URL:
    # fallback to sqlite in project db folder
    os.makedirs("db", exist_ok=True)
    sqlite_path = os.path.abspath(os.path.join("db", "app_fallback.sqlite"))
    sqlite_url = f"sqlite:///{sqlite_path}"
    engine = _make_engine(sqlite_url)
    print(f"Using fallback SQLite DB at {sqlite_path}")

# create session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
