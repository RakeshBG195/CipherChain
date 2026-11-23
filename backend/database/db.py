from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import DB_URL
from backend.database.base import Base

# SQLite needs a special connection argument; PostgreSQL does not.
connect_args = (
    {"check_same_thread": False}
    if DB_URL.startswith("sqlite")
    else {}
)

engine = create_engine(DB_URL, connect_args=connect_args)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def init_db():
    import backend.models.models  # noqa: F401
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()