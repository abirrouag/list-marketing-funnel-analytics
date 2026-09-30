"""
Database connection and session helper for SQLite and PostgreSQL.
"""

import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def get_db_url():
    """
    Constructs Database Connection URL based on environment variables.
    Defaults to SQLite if Postgres credentials are not active.
    """
    db_type = os.getenv("DB_TYPE", "sqlite").lower()
    
    if db_type == "postgres":
        user = os.getenv("POSTGRES_USER", "olist_user")
        pwd = os.getenv("POSTGRES_PASSWORD", "olist_password")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "olist_dw")
        return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
    else:
        db_path = os.getenv("DB_FILE", "data/processed/marketing_funnel_dw.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return f"sqlite:///{db_path}"

def get_engine():
    """Returns SQLAlchemy Engine."""
    url = get_db_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, echo=False)

if __name__ == "__main__":
    eng = get_engine()
    print("Database Engine initialized successfully:", eng.url)
