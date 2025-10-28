"""
Database connection and session management
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging
from typing import Optional
from fastapi import HTTPException

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
            # Default PostgreSQL credentials
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = os.getenv('DB_PORT', '5432')
            db_name = os.getenv('DB_NAME', 'educational_tutor')
            db_user = os.getenv('DB_USER', 'postgres')
            db_password = os.getenv('DB_PASSWORD', 'postgres')  # Using 'postgres' as default password
            
            database_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
        
        logger.info(f"Connecting to database: {db_user}@{db_host}:{db_port}/{db_name}")
        
        # First, try to create the database if it doesn't exist
        self._ensure_database_exists(db_host, db_port, db_user, db_password, db_name)
        
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
    
    def _ensure_database_exists(self, host: str, port: str, user: str, password: str, db_name: str):
        """Create database if it doesn't exist"""
        try:
            # Connect to default postgres database
            engine_temp = create_engine(
                f'postgresql://{user}:{password}@{host}:{port}/postgres',
                isolation_level="AUTOCOMMIT"
            )
            
            with engine_temp.connect() as conn:
                # Check if database exists
                result = conn.execute(
                    text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
                )
                exists = result.fetchone() is not None
                
                if not exists:
                    logger.info(f"Creating database '{db_name}'...")
                    conn.execute(text(f"CREATE DATABASE {db_name}"))
                    logger.info(f"Database '{db_name}' created successfully")
                else:
                    logger.info(f"Database '{db_name}' already exists")
            
            engine_temp.dispose()
            
        except Exception as e:
            logger.error(f"Failed to ensure database exists: {e}")
            logger.error("Please ensure PostgreSQL is running and accessible")
            logger.error("You can manually create the database with:")
            logger.error(f"  CREATE DATABASE {db_name};")
            raise
    
    def get_session(self) -> Session:
        """Get database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call initialize() first.")
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
    if not db_manager.SessionLocal:
        raise HTTPException(
            status_code=500,
            detail="Database not initialized. Please check database configuration."
        )
    
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()
