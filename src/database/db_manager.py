"""
Database connection and session management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging
from typing import Optional

from database.educational_models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        
    def initialize(self, database_url: Optional[str] = None):
        """Initialize database connection"""
        if not database_url:
            database_url = os.getenv(
                'DATABASE_URL',
                'postgresql://postgres:password@localhost:5432/educational_tutor'
            )
        
        # Create engine with connection pooling
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,
            echo=False
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database initialized successfully")
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()


# Global database manager
db_manager = DatabaseManager()


# Dependency for FastAPI
def get_db():
    """FastAPI dependency for database sessions"""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()
