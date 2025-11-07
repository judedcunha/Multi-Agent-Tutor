"""
CRUD operations for educational data
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid

from .educational_models import (
    Student, LearningSession, LearningInteraction,
    StudentProgress, StudentPreference,
    LearningAnalytics, PracticeAnalytics, TopicAnalytics, DailyMetrics
)
from sqlalchemy import func, and_, or_, desc


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


class AnalyticsCRUD:
    """CRUD operations for analytics data"""
    
    @staticmethod
    def create_learning_analytics(db: Session, session_id: str, 
                                  student_id: str) -> LearningAnalytics:
        """Create learning analytics record"""
        analytics = LearningAnalytics(
            analytics_id=str(uuid.uuid4()),
            session_id=session_id,
            student_id=student_id
        )
        db.add(analytics)
        db.commit()
        db.refresh(analytics)
        return analytics
    
    @staticmethod
    def update_learning_analytics(db: Session, session_id: str, **kwargs) -> Optional[LearningAnalytics]:
        """Update learning analytics"""
        analytics = db.query(LearningAnalytics).filter(
            LearningAnalytics.session_id == session_id
        ).first()
        
        if analytics:
            for key, value in kwargs.items():
                if hasattr(analytics, key):
                    setattr(analytics, key, value)
            analytics.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(analytics)
        return analytics
    
    @staticmethod
    def create_practice_analytics(db: Session, session_id: str, student_id: str,
                                 problem_data: Dict[str, Any]) -> PracticeAnalytics:
        """Record practice problem analytics"""
        practice = PracticeAnalytics(
            practice_id=str(uuid.uuid4()),
            session_id=session_id,
            student_id=student_id,
            **problem_data
        )
        db.add(practice)
        db.commit()
        db.refresh(practice)
        return practice
    
    @staticmethod
    def get_or_create_topic_analytics(db: Session, student_id: str, 
                                      topic: str, subject: str) -> TopicAnalytics:
        """Get or create topic analytics"""
        topic_analytics = db.query(TopicAnalytics).filter(
            TopicAnalytics.student_id == student_id,
            TopicAnalytics.topic == topic
        ).first()
        
        if not topic_analytics:
            topic_analytics = TopicAnalytics(
                student_id=student_id,
                topic=topic,
                subject=subject
            )
            db.add(topic_analytics)
            db.commit()
            db.refresh(topic_analytics)
        
        return topic_analytics
    
    @staticmethod
    def update_topic_analytics(db: Session, student_id: str, topic: str,
                              **metrics) -> Optional[TopicAnalytics]:
        """Update topic analytics metrics"""
        topic_analytics = AnalyticsCRUD.get_or_create_topic_analytics(
            db, student_id, topic, metrics.get('subject', 'general')
        )
        
        # Increment counters
        if 'request_count' in metrics:
            topic_analytics.request_count += metrics['request_count']
        if 'practice_attempted' in metrics:
            topic_analytics.practice_attempted += metrics['practice_attempted']
        if 'practice_correct' in metrics:
            topic_analytics.practice_correct += metrics['practice_correct']
        if 'session_time' in metrics:
            topic_analytics.total_time_minutes += metrics['session_time']
        
        # Update calculations
        if topic_analytics.practice_attempted > 0:
            topic_analytics.success_rate = (
                topic_analytics.practice_correct / topic_analytics.practice_attempted
            )
        
        topic_analytics.last_accessed = datetime.utcnow()
        db.commit()
        return topic_analytics
    
    @staticmethod
    def get_daily_metrics(db: Session, student_id: str, date: datetime) -> Optional[DailyMetrics]:
        """Get daily metrics for a student"""
        start_of_day = datetime.combine(date.date(), datetime.min.time())
        return db.query(DailyMetrics).filter(
            DailyMetrics.student_id == student_id,
            DailyMetrics.date == start_of_day
        ).first()
    
    @staticmethod
    def create_or_update_daily_metrics(db: Session, student_id: str,
                                       date: datetime, metrics: Dict[str, Any]) -> DailyMetrics:
        """Create or update daily metrics"""
        start_of_day = datetime.combine(date.date(), datetime.min.time())
        
        daily_metric = AnalyticsCRUD.get_daily_metrics(db, student_id, date)
        
        if not daily_metric:
            daily_metric = DailyMetrics(
                student_id=student_id,
                date=start_of_day
            )
            db.add(daily_metric)
        
        # Update metrics
        for key, value in metrics.items():
            if hasattr(daily_metric, key):
                setattr(daily_metric, key, value)
        
        db.commit()
        db.refresh(daily_metric)
        return daily_metric
    
    @staticmethod
    def get_student_analytics_summary(db: Session, student_id: str,
                                      days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics summary for a student"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Session stats
        session_stats = db.query(
            func.count(LearningSession.id).label('total_sessions'),
            func.sum(LearningSession.duration_minutes).label('total_time')
        ).filter(
            LearningSession.student_id == student_id,
            LearningSession.started_at >= start_date
        ).first()
        
        # Practice stats
        practice_stats = db.query(
            func.count(PracticeAnalytics.id).label('total_problems'),
            func.sum(PracticeAnalytics.correct.cast(db.Integer)).label('correct_problems')
        ).filter(
            PracticeAnalytics.student_id == student_id,
            PracticeAnalytics.timestamp >= start_date
        ).first()
        
        # Top topics
        top_topics = db.query(TopicAnalytics).filter(
            TopicAnalytics.student_id == student_id
        ).order_by(desc(TopicAnalytics.request_count)).limit(5).all()
        
        # Recent activity
        recent_sessions = db.query(LearningSession).filter(
            LearningSession.student_id == student_id,
            LearningSession.started_at >= start_date
        ).order_by(desc(LearningSession.started_at)).limit(10).all()
        
        return {
            'period_days': days,
            'sessions': {
                'total': session_stats.total_sessions or 0,
                'total_time_hours': (session_stats.total_time or 0) / 60
            },
            'practice': {
                'total_problems': practice_stats.total_problems or 0,
                'correct_problems': practice_stats.correct_problems or 0,
                'accuracy': (
                    (practice_stats.correct_problems or 0) / (practice_stats.total_problems or 1)
                    if practice_stats.total_problems else 0
                )
            },
            'top_topics': [
                {
                    'topic': t.topic,
                    'subject': t.subject,
                    'sessions': t.total_sessions,
                    'mastery': t.mastery_level
                }
                for t in top_topics
            ],
            'recent_sessions': [
                {
                    'session_id': s.session_id,
                    'topic': s.topic,
                    'duration': s.duration_minutes,
                    'date': s.started_at.isoformat()
                }
                for s in recent_sessions
            ]
        }
    
    @staticmethod
    def get_topic_trends(db: Session, student_id: str, topic: str,
                        days: int = 30) -> List[Dict[str, Any]]:
        """Get performance trends for a specific topic"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get practice history
        practice_history = db.query(PracticeAnalytics).filter(
            PracticeAnalytics.student_id == student_id,
            PracticeAnalytics.topic == topic,
            PracticeAnalytics.timestamp >= start_date
        ).order_by(PracticeAnalytics.timestamp).all()
        
        trends = []
        for practice in practice_history:
            trends.append({
                'date': practice.timestamp.isoformat(),
                'correct': practice.correct,
                'difficulty': practice.difficulty,
                'time_spent': practice.time_spent_seconds,
                'hints_used': practice.hints_used
            })
        
        return trends
    
    @staticmethod
    def calculate_learning_streak(db: Session, student_id: str) -> Dict[str, int]:
        """Calculate learning streaks for a student"""
        # Get daily metrics for the last 90 days
        start_date = datetime.utcnow() - timedelta(days=90)
        
        daily_metrics = db.query(DailyMetrics).filter(
            DailyMetrics.student_id == student_id,
            DailyMetrics.date >= start_date
        ).order_by(desc(DailyMetrics.date)).all()
        
        if not daily_metrics:
            return {'current_streak': 0, 'longest_streak': 0}
        
        # Calculate current streak
        current_streak = 0
        today = datetime.utcnow().date()
        
        for metric in daily_metrics:
            expected_date = today - timedelta(days=current_streak)
            if metric.date.date() == expected_date and metric.is_active_day:
                current_streak += 1
            else:
                break
        
        # Calculate longest streak
        longest_streak = current_streak
        temp_streak = 0
        
        for i in range(len(daily_metrics)):
            if daily_metrics[i].is_active_day:
                if i == 0 or (
                    daily_metrics[i-1].date.date() == 
                    daily_metrics[i].date.date() + timedelta(days=1)
                ):
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 1
            else:
                temp_streak = 0
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak
        }


# Global Analytics CRUD instance
analytics_crud = AnalyticsCRUD()
