"""
CRUD operations for educational data
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid

from database.educational_models import (
    Student, LearningSession, LearningInteraction,
    StudentProgress, StudentPreference
)


class EducationalCRUD:
    """CRUD operations for educational data"""
    
    @staticmethod
    def create_student(db: Session, name: str, email: Optional[str] = None,
                       level: str = "beginner", learning_style: str = "mixed") -> Student:
        """Create new student"""
        student = Student(
            student_id=str(uuid.uuid4()),
            name=name,
            email=email,
            level=level,
            learning_style=learning_style
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        return student
    
    @staticmethod
    def get_student(db: Session, student_id: str) -> Optional[Student]:
        """Get student by ID"""
        return db.query(Student).filter(Student.student_id == student_id).first()
    
    @staticmethod
    def get_student_by_email(db: Session, email: str) -> Optional[Student]:
        """Get student by email"""
        return db.query(Student).filter(Student.email == email).first()
    
    @staticmethod
    def update_student(db: Session, student_id: str, **kwargs) -> Optional[Student]:
        """Update student information"""
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if student:
            for key, value in kwargs.items():
                if hasattr(student, key):
                    setattr(student, key, value)
            student.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(student)
        return student
    
    @staticmethod
    def create_learning_session(db: Session, student_id: str, topic: str,
                                subject: str, level: str) -> LearningSession:
        """Create new learning session"""
        session = LearningSession(
            session_id=str(uuid.uuid4()),
            student_id=student_id,
            topic=topic,
            subject=subject,
            level=level
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def update_session_results(db: Session, session_id: str,
                               lesson_plan: Dict, practice_problems: List[Dict],
                               assessment_results: Dict, agents_used: List[str]):
        """Update session with results"""
        session = db.query(LearningSession).filter(
            LearningSession.session_id == session_id
        ).first()
        
        if session:
            session.lesson_plan = lesson_plan
            session.practice_problems = practice_problems
            session.assessment_results = assessment_results
            session.agents_used = agents_used
            session.completed_at = datetime.utcnow()
            
            # Calculate duration
            if session.started_at:
                duration = (session.completed_at - session.started_at).total_seconds() / 60
                session.duration_minutes = duration
            
            db.commit()
    
    @staticmethod
    def track_student_progress(db: Session, student_id: str, subject: str,
                               topic: str, success: bool, time_spent: float):
        """Track student progress"""
        progress = db.query(StudentProgress).filter(
            StudentProgress.student_id == student_id,
            StudentProgress.subject == subject,
            StudentProgress.topic == topic
        ).first()
        
        if not progress:
            progress = StudentProgress(
                progress_id=str(uuid.uuid4()),
                student_id=student_id,
                subject=subject,
                topic=topic
            )
            db.add(progress)
        
        # Update metrics
        progress.practice_count += 1
        if success:
            progress.correct_count += 1
        progress.total_time_minutes += time_spent
        progress.last_practiced = datetime.utcnow()
        
        # Update mastery level
        if progress.practice_count > 0:
            progress.mastery_level = progress.correct_count / progress.practice_count
        
        db.commit()
        return progress
    
    @staticmethod
    def create_interaction(db: Session, session_id: str, interaction_type: str,
                          agent_name: str, student_input: Optional[str],
                          agent_response: str, response_time_ms: int) -> LearningInteraction:
        """Record a learning interaction"""
        interaction = LearningInteraction(
            interaction_id=str(uuid.uuid4()),
            session_id=session_id,
            interaction_type=interaction_type,
            agent_name=agent_name,
            student_input=student_input,
            agent_response=agent_response,
            response_time_ms=response_time_ms
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        return interaction
    
    @staticmethod
    def get_student_history(db: Session, student_id: str,
                            limit: int = 10) -> List[LearningSession]:
        """Get student's learning history"""
        return db.query(LearningSession).filter(
            LearningSession.student_id == student_id
        ).order_by(LearningSession.started_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_student_progress_summary(db: Session, student_id: str) -> Dict[str, Any]:
        """Get comprehensive progress summary"""
        progress_records = db.query(StudentProgress).filter(
            StudentProgress.student_id == student_id
        ).all()
        
        summary = {
            "total_topics": len(progress_records),
            "mastered_topics": len([p for p in progress_records if p.mastery_level > 0.8]),
            "in_progress_topics": len([p for p in progress_records if 0.3 < p.mastery_level <= 0.8]),
            "subjects": {}
        }
        
        # Group by subject
        for progress in progress_records:
            if progress.subject not in summary["subjects"]:
                summary["subjects"][progress.subject] = {
                    "topics": [],
                    "average_mastery": 0,
                    "total_time": 0
                }
            
            summary["subjects"][progress.subject]["topics"].append({
                "topic": progress.topic,
                "mastery": progress.mastery_level,
                "practice_count": progress.practice_count
            })
            summary["subjects"][progress.subject]["total_time"] += progress.total_time_minutes
        
        # Calculate averages
        for subject in summary["subjects"]:
            topics = summary["subjects"][subject]["topics"]
            if topics:
                avg_mastery = sum(t["mastery"] for t in topics) / len(topics)
                summary["subjects"][subject]["average_mastery"] = avg_mastery
        
        return summary
    
    @staticmethod
    def set_student_preference(db: Session, student_id: str,
                               preference_type: str, preference_value: str) -> StudentPreference:
        """Set or update student preference"""
        # Check if preference exists
        preference = db.query(StudentPreference).filter(
            StudentPreference.student_id == student_id,
            StudentPreference.preference_type == preference_type
        ).first()
        
        if preference:
            preference.preference_value = preference_value
        else:
            preference = StudentPreference(
                student_id=student_id,
                preference_type=preference_type,
                preference_value=preference_value
            )
            db.add(preference)
        
        db.commit()
        db.refresh(preference)
        return preference
    
    @staticmethod
    def get_student_preferences(db: Session, student_id: str) -> List[StudentPreference]:
        """Get all preferences for a student"""
        return db.query(StudentPreference).filter(
            StudentPreference.student_id == student_id
        ).all()
    
    @staticmethod
    def delete_student(db: Session, student_id: str) -> bool:
        """Delete student and all related data (GDPR compliance)"""
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if student:
            # Delete related data first
            db.query(StudentProgress).filter(
                StudentProgress.student_id == student_id
            ).delete()
            db.query(StudentPreference).filter(
                StudentPreference.student_id == student_id
            ).delete()
            
            # Delete sessions and interactions
            sessions = db.query(LearningSession).filter(
                LearningSession.student_id == student_id
            ).all()
            for session in sessions:
                db.query(LearningInteraction).filter(
                    LearningInteraction.session_id == session.session_id
                ).delete()
            db.query(LearningSession).filter(
                LearningSession.student_id == student_id
            ).delete()
            
            # Finally, delete student
            db.delete(student)
            db.commit()
            return True
        return False


# Global CRUD instance
educational_crud = EducationalCRUD()
