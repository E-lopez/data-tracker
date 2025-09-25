from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()
engine = None
SessionLocal = None

def init_db():
    """Initialize database connection for Lambda"""
    global engine, SessionLocal
    
    if engine is None:
        config = Config()
        engine = create_engine(
            config.SQLALCHEMY_DATABASE_URI,
            **config.SQLALCHEMY_ENGINE_OPTIONS
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Import all models to register them with Base
        from models.loan_metadata import LoanMetadata
        from models.loan_tables import LoanTables
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)

    return SessionLocal

def get_db_session():
    """Get database session"""
    if SessionLocal is None:
        init_db()
    return SessionLocal()

def close_db_session(session):
    """Close database session"""
    if session:
        try:
            session.close()
        except Exception as e:
            logger.error(f"Error closing session: {e}")

class DatabaseSession:
    """Context manager for database sessions"""
    def __init__(self):
        self.session = None
    
    def __enter__(self):
        self.session = get_db_session()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            try:
                if exc_type:
                    self.session.rollback()
                else:
                    self.session.commit()
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
                self.session.rollback()
            finally:
                self.session.close()