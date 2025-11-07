"""
Database module for educational tutor application.

This module provides:
- Database connection and session management
- SQLAlchemy models for educational data
- CRUD operations for educational and analytics data
- Session dependency for FastAPI
"""

from .educational_models import (
    Base,
    Student,
    LearningSession,
    LearningInteraction,
    StudentProgress,
    StudentPreference,
    ContentCache,
    LearningAnalytics,
    PracticeAnalytics,
    TopicAnalytics,
    DailyMetrics
)

from .db_manager import (
    DatabaseManager,
    db_manager,
    get_db
)

from .educational_crud import (
    EducationalCRUD,
    educational_crud,
    AnalyticsCRUD,
    analytics_crud
)


# Public API
__all__ = [
    # Models
    "Base",
    "Student",
    "LearningSession",
    "LearningInteraction",
    "StudentProgress",
    "StudentPreference",
    "ContentCache",
    "LearningAnalytics",
    "PracticeAnalytics",
    "TopicAnalytics",
    "DailyMetrics",
    
    # Database Management
    "DatabaseManager",
    "db_manager",
    "get_db",
    
    # CRUD Operations
    "EducationalCRUD",
    "educational_crud",
    "AnalyticsCRUD",
    "analytics_crud",
]