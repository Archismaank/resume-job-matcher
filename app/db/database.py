
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database file will be created in the project root
SQLALCHEMY_DATABASE_URL = "sqlite:///./resume_matcher.db"

# Create the SQLAlchemy engine
# check_same_thread=False is required for SQLite when used with FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Each request gets its own database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all ORM models will inherit from
Base = declarative_base()


def get_db():
    """
    FastAPI dependency — yields a database session per request,
    and always closes it when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Creates all tables defined via Base subclasses.
    Called once on server startup.
    """
    from app.db.models import User, AnalysisHistory, RecommendationHistory  # noqa: F401

    Base.metadata.create_all(bind=engine)
