"""
SQLAlchemy models for educational data persistence
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(String(50), unique=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, nullable=True)
    level = Column(String(20), default='beginner')
    learning_style = Column(String(20), default='mixed')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("LearningSession", back_populates="student")
    progress = relationship("StudentProgress", back_populates="student")
    preferences = relationship("StudentPreference", back_populates="student")


class LearningSession(Base):
    __tablename__ = 'learning_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), unique=True, index=True)
    student_id = Column(String(50), ForeignKey('students.student_id'))
    topic = Column(String(200))
    subject = Column(String(50))
    level = Column(String(20))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    
    # Session data
    lesson_plan = Column(JSON)
    practice_problems = Column(JSON)
    assessment_results = Column(JSON)
    agents_used = Column(JSON)
    
    # Performance metrics
    engagement_score = Column(Float, nullable=True)
    completion_rate = Column(Float, nullable=True)
    understanding_score = Column(Float, nullable=True)
    
    # Relationships
    student = relationship("Student", back_populates="sessions")
    interactions = relationship("LearningInteraction", back_populates="session")


class LearningInteraction(Base):
    __tablename__ = 'learning_interactions'
    
    id = Column(Integer, primary_key=True)
    interaction_id = Column(String(50), unique=True)
    session_id = Column(String(50), ForeignKey('learning_sessions.session_id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    interaction_type = Column(String(50))  # question, answer, hint_request, etc.
    agent_name = Column(String(50))
    
    # Interaction data
    student_input = Column(Text, nullable=True)
    agent_response = Column(Text)
    response_time_ms = Column(Integer)
    
    # Quality metrics
    was_helpful = Column(Boolean, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Relationship
    session = relationship("LearningSession", back_populates="interactions")


class StudentProgress(Base):
    __tablename__ = 'student_progress'
    
    id = Column(Integer, primary_key=True)
    progress_id = Column(String(50), unique=True)
    student_id = Column(String(50), ForeignKey('students.student_id'))
    subject = Column(String(50))
    topic = Column(String(200))
    
    # Progress metrics
    mastery_level = Column(Float, default=0.0)  # 0.0 to 1.0
    practice_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    total_time_minutes = Column(Float, default=0.0)
    last_practiced = Column(DateTime, nullable=True)
    
    # Learning path
    current_level = Column(String(20), default='beginner')
    next_topics = Column(JSON, nullable=True)
    prerequisites_completed = Column(JSON, nullable=True)
    
    # Relationship
    student = relationship("Student", back_populates="progress")


class StudentPreference(Base):
    __tablename__ = 'student_preferences'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(String(50), ForeignKey('students.student_id'))
    preference_type = Column(String(50))  # difficulty, pace, content_type, etc.
    preference_value = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    student = relationship("Student", back_populates="preferences")


class ContentCache(Base):
    __tablename__ = 'content_cache'
    
    id = Column(Integer, primary_key=True)
    cache_key = Column(String(200), unique=True, index=True)
    content_type = Column(String(50))  # lesson, practice, explanation
    content = Column(JSON)
    cache_metadata = Column(JSON)  
    created_at = Column(DateTime, default=datetime.utcnow)
    accessed_at = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=1)
    ttl_hours = Column(Integer, default=24)
