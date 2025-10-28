"""
Unit tests for Phase 3 database operations
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from database.educational_models import Base, Student, LearningSession, StudentProgress
from database.educational_crud import EducationalCRUD
from database.db_manager import DatabaseManager


# Test database configuration
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create a test database session"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestStudentCRUD:
    """Test Student CRUD operations"""
    
    def test_create_student(self, test_db):
        """Test creating a new student"""
        student = EducationalCRUD.create_student(
            test_db,
            name="Test Student",
            email="test@example.com",
            level="beginner",
            learning_style="visual"
        )
        
        assert student.name == "Test Student"
        assert student.email == "test@example.com"
        assert student.level == "beginner"
        assert student.learning_style == "visual"
        assert student.student_id is not None
    
    def test_get_student(self, test_db):
        """Test retrieving a student"""
        # Create student
        student = EducationalCRUD.create_student(
            test_db, "Test Student", "test@example.com"
        )
        
        # Retrieve student
        retrieved = EducationalCRUD.get_student(test_db, student.student_id)
        assert retrieved is not None
        assert retrieved.name == "Test Student"
        assert retrieved.email == "test@example.com"
    
    def test_get_student_by_email(self, test_db):
        """Test retrieving student by email"""
        # Create student
        student = EducationalCRUD.create_student(
            test_db, "Test Student", "test@example.com"
        )
        
        # Retrieve by email
        retrieved = EducationalCRUD.get_student_by_email(test_db, "test@example.com")
        assert retrieved is not None
        assert retrieved.student_id == student.student_id
    
    def test_update_student(self, test_db):
        """Test updating student information"""
        # Create student
        student = EducationalCRUD.create_student(
            test_db, "Test Student", "test@example.com"
        )
        
        # Update student
        updated = EducationalCRUD.update_student(
            test_db,
            student.student_id,
            level="intermediate",
            learning_style="kinesthetic"
        )
        
        assert updated.level == "intermediate"
        assert updated.learning_style == "kinesthetic"
    
    def test_delete_student(self, test_db):
        """Test deleting a student"""
        # Create student
        student = EducationalCRUD.create_student(
            test_db, "Test Student", "test@example.com"
        )
        
        # Delete student
        result = EducationalCRUD.delete_student(test_db, student.student_id)
        assert result is True
        
        # Verify deletion
        retrieved = EducationalCRUD.get_student(test_db, student.student_id)
        assert retrieved is None


class TestLearningSessionCRUD:
    """Test Learning Session CRUD operations"""
    
    def test_create_learning_session(self, test_db):
        """Test creating a learning session"""
        # Create student first
        student = EducationalCRUD.create_student(test_db, "Test Student")
        
        # Create session
        session = EducationalCRUD.create_learning_session(
            test_db,
            student.student_id,
            "Python Basics",
            "Programming",
            "beginner"
        )
        
        assert session.topic == "Python Basics"
        assert session.subject == "Programming"
        assert session.level == "beginner"
        assert session.session_id is not None
    
    def test_update_session_results(self, test_db):
        """Test updating session with results"""
        # Create student and session
        student = EducationalCRUD.create_student(test_db, "Test Student")
        session = EducationalCRUD.create_learning_session(
            test_db,
            student.student_id,
            "Python Basics",
            "Programming",
            "beginner"
        )
        
        # Update with results
        lesson_plan = {"objectives": ["Learn variables", "Learn functions"]}
        practice_problems = [{"problem": "Write a function", "difficulty": "easy"}]
        assessment_results = {"score": 0.85, "passed": True}
        agents_used = ["subject_expert", "practice_generator"]
        
        EducationalCRUD.update_session_results(
            test_db,
            session.session_id,
            lesson_plan,
            practice_problems,
            assessment_results,
            agents_used
        )
        
        # Retrieve and verify
        updated_session = test_db.query(LearningSession).filter(
            LearningSession.session_id == session.session_id
        ).first()
        
        assert updated_session.lesson_plan == lesson_plan
        assert updated_session.practice_problems == practice_problems
        assert updated_session.assessment_results == assessment_results
        assert updated_session.agents_used == agents_used
        assert updated_session.completed_at is not None
        assert updated_session.duration_minutes is not None
    
    def test_get_student_history(self, test_db):
        """Test retrieving student's learning history"""
        # Create student
        student = EducationalCRUD.create_student(test_db, "Test Student")
        
        # Create multiple sessions
        for i in range(3):
            EducationalCRUD.create_learning_session(
                test_db,
                student.student_id,
                f"Topic {i}",
                "Subject",
                "beginner"
            )
        
        # Get history
        history = EducationalCRUD.get_student_history(test_db, student.student_id)
        assert len(history) == 3
        assert all(s.student_id == student.student_id for s in history)


class TestStudentProgress:
    """Test Student Progress tracking"""
    
    def test_track_student_progress(self, test_db):
        """Test tracking student progress"""
        # Create student
        student = EducationalCRUD.create_student(test_db, "Test Student")
        
        # Track progress
        progress = EducationalCRUD.track_student_progress(
            test_db,
            student.student_id,
            "Mathematics",
            "Algebra",
            success=True,
            time_spent=30.0
        )
        
        assert progress.subject == "Mathematics"
        assert progress.topic == "Algebra"
        assert progress.practice_count == 1
        assert progress.correct_count == 1
        assert progress.total_time_minutes == 30.0
        assert progress.mastery_level == 1.0
    
    def test_progress_summary(self, test_db):
        """Test getting progress summary"""
        # Create student
        student = EducationalCRUD.create_student(test_db, "Test Student")
        
        # Track multiple progress entries
        EducationalCRUD.track_student_progress(
            test_db, student.student_id, "Math", "Algebra", True, 30
        )
        EducationalCRUD.track_student_progress(
            test_db, student.student_id, "Math", "Geometry", True, 25
        )
        EducationalCRUD.track_student_progress(
            test_db, student.student_id, "Science", "Physics", False, 20
        )
        
        # Get summary
        summary = EducationalCRUD.get_student_progress_summary(
            test_db, student.student_id
        )
        
        assert summary["total_topics"] == 3
        assert summary["mastered_topics"] == 2  # Algebra and Geometry
        assert "Math" in summary["subjects"]
        assert "Science" in summary["subjects"]


class TestStudentPreferences:
    """Test Student Preferences"""
    
    def test_set_preference(self, test_db):
        """Test setting student preference"""
        # Create student
        student = EducationalCRUD.create_student(test_db, "Test Student")
        
        # Set preference
        pref = EducationalCRUD.set_student_preference(
            test_db,
            student.student_id,
            "difficulty",
            "intermediate"
        )
        
        assert pref.preference_type == "difficulty"
        assert pref.preference_value == "intermediate"
    
    def test_update_preference(self, test_db):
        """Test updating existing preference"""
        # Create student
        student = EducationalCRUD.create_student(test_db, "Test Student")
        
        # Set initial preference
        EducationalCRUD.set_student_preference(
            test_db, student.student_id, "pace", "slow"
        )
        
        # Update preference
        updated = EducationalCRUD.set_student_preference(
            test_db, student.student_id, "pace", "normal"
        )
        
        # Verify update
        prefs = EducationalCRUD.get_student_preferences(test_db, student.student_id)
        pace_prefs = [p for p in prefs if p.preference_type == "pace"]
        
        assert len(pace_prefs) == 1
        assert pace_prefs[0].preference_value == "normal"


class TestLearningInteraction:
    """Test Learning Interaction tracking"""
    
    def test_create_interaction(self, test_db):
        """Test creating a learning interaction"""
        # Create student and session
        student = EducationalCRUD.create_student(test_db, "Test Student")
        session = EducationalCRUD.create_learning_session(
            test_db,
            student.student_id,
            "Python",
            "Programming",
            "beginner"
        )
        
        # Create interaction
        interaction = EducationalCRUD.create_interaction(
            test_db,
            session.session_id,
            "question",
            "subject_expert",
            "What is a variable?",
            "A variable is a container for storing data values.",
            250
        )
        
        assert interaction.interaction_type == "question"
        assert interaction.agent_name == "subject_expert"
        assert interaction.student_input == "What is a variable?"
        assert interaction.response_time_ms == 250


class TestDatabaseManager:
    """Test Database Manager"""
    
    def test_initialize(self):
        """Test database initialization"""
        manager = DatabaseManager()
        manager.initialize("sqlite:///:memory:")
        
        assert manager.engine is not None
        assert manager.SessionLocal is not None
        
        # Clean up
        manager.close()
    
    def test_get_session(self):
        """Test getting a session"""
        manager = DatabaseManager()
        manager.initialize("sqlite:///:memory:")
        
        session = manager.get_session()
        assert session is not None
        
        session.close()
        manager.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
