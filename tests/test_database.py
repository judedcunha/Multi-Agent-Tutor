"""
Test suite for database operations and models
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

# Project imports - using actual model names from educational_models
from database.educational_models import (
    Base, Student, LearningSession, StudentProgress, 
    LearningInteraction, StudentPreference
)
from database.educational_crud import EducationalCRUD, educational_crud, analytics_crud
from database.db_manager import DatabaseManager


class TestDatabaseModels:
    """Test suite for database models"""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_database):
        """Setup test database session"""
        self.session = test_database
        
    @pytest.mark.unit
    def test_student_model_creation(self):
        """Test Student model creation and properties"""
        student = Student(
            student_id="test_student_123",
            name="Test Student",
            email="test@example.com",
            level="intermediate",
            learning_style="visual"
        )
        
        self.session.add(student)
        self.session.commit()
        
        # Verify student was created
        saved_student = self.session.query(Student).filter_by(email="test@example.com").first()
        assert saved_student is not None
        assert saved_student.name == "Test Student"
        assert saved_student.level == "intermediate"
        assert saved_student.created_at is not None
    
    @pytest.mark.unit
    def test_learning_session_creation(self):
        """Test LearningSession model creation"""
        # Create student first
        student = Student(
            student_id="student_456",
            name="Test Student",
            email="student@example.com"
        )
        self.session.add(student)
        self.session.commit()
        
        # Create learning session
        session = LearningSession(
            session_id="session_789",
            student_id=student.student_id,
            topic="Python Basics",
            subject="Programming",
            level="beginner"
        )
        
        self.session.add(session)
        self.session.commit()
        
        # Verify session was created
        saved_session = self.session.query(LearningSession).first()
        assert saved_session is not None
        assert saved_session.topic == "Python Basics"
        assert saved_session.subject == "Programming"


class TestDatabaseOperations:
    """Test suite for database operations"""
    
    @pytest.mark.unit
    def test_create_student_operation(self, test_database):
        """Test creating student through CRUD operations"""
        # Use static method with db parameter
        student = EducationalCRUD.create_student(
            db=test_database,
            name="New Student",
            email="newstudent@example.com",
            level="beginner"
        )
        
        assert student.student_id is not None
        assert student.name == "New Student"
        assert student.email == "newstudent@example.com"
    
    @pytest.mark.unit
    def test_get_student_by_email(self, test_database):
        """Test retrieving student by email"""
        # Create student first
        EducationalCRUD.create_student(
            db=test_database,
            name="Find Me",
            email="findme@example.com"
        )
        
        # Find student using static method
        found_student = EducationalCRUD.get_student_by_email(db=test_database, email="findme@example.com")
        
        assert found_student is not None
        assert found_student.name == "Find Me"


class TestDatabaseIntegration:
    """Integration tests for database system"""
    
    @pytest.mark.integration
    def test_student_session_relationship(self, test_database):
        """Test relationship between students and learning sessions"""
        # Use static methods - no need to instantiate
        
        # Create student
        student = Student(
            student_id="related_student_001",
            name="Related Student",
            email="related@example.com"
        )
        test_database.add(student)
        test_database.commit()
        
        # Create multiple sessions
        for i in range(3):
            session = LearningSession(
                session_id=f"session_{i}",
                student_id=student.student_id,
                topic=f"Topic {i}",
                subject="Test"
            )
            test_database.add(session)
        
        test_database.commit()
        
        # Query student with sessions
        student_with_sessions = test_database.query(Student).filter_by(
            email="related@example.com"
        ).first()
        
        sessions = test_database.query(LearningSession).filter_by(
            student_id=student_with_sessions.student_id
        ).all()
        
        assert len(sessions) == 3
