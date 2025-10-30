"""
Educational Analytics Manager
Handles collection, storage, and retrieval of learning analytics
"""

import logging
import json
import uuid
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, Integer

from database.educational_models import (
    LearningAnalytics,
    PracticeAnalytics,
    TopicAnalytics,
    DailyMetrics,
    LearningSession,
    Student
)
from database.db_manager import db_manager
from optimization.educational_caching import cache_manager

logger = logging.getLogger(__name__)


class AnalyticsManager:
    """
    Manages educational analytics collection and retrieval
    All methods are synchronous and non-blocking using threading where needed
    """
    
    def __init__(self):
        """Initialize the analytics manager"""
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.initialized = False
        logger.info("AnalyticsManager initialized")
    
    def initialize(self):
        """Initialize analytics system"""
        try:
            # Ensure database is initialized
            if not self.db_manager.engine:
                self.db_manager.initialize()
            
            # Ensure cache is initialized for real-time metrics
            if not self.cache_manager.redis_client:
                self.cache_manager.initialize()
            
            self.initialized = True
            logger.info("Analytics system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize analytics: {e}")
            self.initialized = False
    
    # ==================== Recording Metrics ====================
    
    def record_session_start(
        self,
        session_id: str,
        student_id: str,
        topic: str,
        subject: str,
        level: str
    ) -> Dict[str, Any]:
        """Record the start of a learning session (non-blocking)"""
        def _record():
            try:
                # Create analytics entry
                analytics_id = str(uuid.uuid4())
                
                with self.db_manager.get_session() as db:
                    analytics = LearningAnalytics(
                        analytics_id=analytics_id,
                        session_id=session_id,
                        student_id=student_id
                    )
                    db.add(analytics)
                    db.commit()
                
                # Cache for real-time tracking
                cache_key = f"analytics:session:{session_id}"
                session_data = {
                    'session_id': session_id,
                    'student_id': student_id,
                    'topic': topic,
                    'subject': subject,
                    'level': level,
                    'start_time': datetime.utcnow().isoformat(),
                    'interactions': []
                }
                
                # Use cache manager's synchronous method
                self.cache_manager.set_with_sliding_expiration(
                    cache_key,
                    session_data,
                    ttl=86400  # 24 hours
                )
                
                logger.info(f"Session started: {session_id} for student {student_id}")
                
            except Exception as e:
                logger.error(f"Error recording session start: {e}")
        
        # Execute in background thread (non-blocking)
        threading.Thread(target=_record, daemon=True).start()
        return {'status': 'recording'}
    
    def record_practice_attempt(
        self,
        session_id: str,
        student_id: str,
        problem_number: int,
        problem_text: str,
        topic: str,
        difficulty: str,
        student_answer: str,
        correct: bool,
        time_spent: int,
        hints_used: int = 0
    ) -> Dict[str, Any]:
        """Record a practice problem attempt (non-blocking)"""
        def _record():
            try:
                practice_id = str(uuid.uuid4())
                
                with self.db_manager.get_session() as db:
                    # Record practice analytics
                    practice = PracticeAnalytics(
                        practice_id=practice_id,
                        session_id=session_id,
                        student_id=student_id,
                        problem_number=problem_number,
                        problem_text=problem_text,
                        topic=topic,
                        difficulty=difficulty,
                        attempts=1,
                        correct=correct,
                        time_spent_seconds=time_spent,
                        hints_used=hints_used,
                        student_answer=student_answer
                    )
                    db.add(practice)
                    
                    # Update session analytics
                    analytics = db.query(LearningAnalytics).filter_by(
                        session_id=session_id
                    ).first()
                    
                    if analytics:
                        analytics.practice_attempted += 1
                        if correct:
                            analytics.practice_correct += 1
                        if analytics.practice_attempted > 0:
                            analytics.practice_accuracy = (
                                analytics.practice_correct / analytics.practice_attempted
                            )
                    
                    db.commit()
                
                # Update topic analytics
                self._update_topic_analytics(
                    student_id, topic, subject=None,
                    practice_attempted=1, practice_correct=1 if correct else 0
                )
                
                logger.info(f"Practice attempt recorded: {practice_id}")
                
            except Exception as e:
                logger.error(f"Error recording practice attempt: {e}")
        
        # Execute in background thread (non-blocking)
        threading.Thread(target=_record, daemon=True).start()
        return {'status': 'recording'}
    
    def record_interaction(
        self,
        session_id: str,
        interaction_type: str,
        agent_name: str,
        response_time_ms: int
    ) -> None:
        """Record an interaction during a session (non-blocking)"""
        def _record():
            try:
                # Update session analytics
                with self.db_manager.get_session() as db:
                    analytics = db.query(LearningAnalytics).filter_by(
                        session_id=session_id
                    ).first()
                    
                    if analytics:
                        analytics.total_interactions += 1
                        
                        if interaction_type == 'question':
                            analytics.questions_asked += 1
                        elif interaction_type == 'hint_request':
                            analytics.hints_requested += 1
                        
                        # Track agent usage
                        agents = analytics.agents_triggered or {}
                        agents[agent_name] = agents.get(agent_name, 0) + 1
                        analytics.agents_triggered = agents
                        
                        db.commit()
                
                # Update real-time cache
                cache_key = f"analytics:session:{session_id}"
                cached_data = self.cache_manager.get_with_sliding_expiration(
                    cache_key, 
                    ttl=86400
                )
                
                if cached_data:
                    cached_data['interactions'].append({
                        'type': interaction_type,
                        'agent': agent_name,
                        'time_ms': response_time_ms,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    self.cache_manager.set_with_sliding_expiration(
                        cache_key,
                        cached_data,
                        ttl=86400
                    )
                    
            except Exception as e:
                logger.error(f"Error recording interaction: {e}")
        
        # Execute in background thread (non-blocking)
        threading.Thread(target=_record, daemon=True).start()
    
    def record_session_end(
        self,
        session_id: str,
        engagement_score: float = None,
        completion_rate: float = None
    ) -> Dict[str, Any]:
        """Record the end of a learning session (non-blocking)"""
        def _record():
            try:
                duration = 0
                with self.db_manager.get_session() as db:
                    # Update session
                    session = db.query(LearningSession).filter_by(
                        session_id=session_id
                    ).first()
                    
                    if session:
                        session.completed_at = datetime.utcnow()
                        duration = (session.completed_at - session.started_at).total_seconds()
                        session.duration_minutes = duration / 60
                    
                    # Update analytics
                    analytics = db.query(LearningAnalytics).filter_by(
                        session_id=session_id
                    ).first()
                    
                    if analytics:
                        analytics.total_time_seconds = int(duration)
                        
                        if engagement_score is not None:
                            analytics.engagement_score = engagement_score
                        
                        if completion_rate is not None:
                            analytics.completion_rate = completion_rate
                        
                        analytics.updated_at = datetime.utcnow()
                    
                    db.commit()
                
                logger.info(f"Session ended: {session_id}")
                
            except Exception as e:
                logger.error(f"Error recording session end: {e}")
        
        # Execute in background thread (non-blocking)
        threading.Thread(target=_record, daemon=True).start()
        return {'status': 'recording'}
    
    # ==================== Retrieving Analytics ====================
    
    def get_student_analytics(
        self,
        student_id: str,
        time_range: str = 'week'  # 'day', 'week', 'month'
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for a student"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            if time_range == 'day':
                start_date = end_date - timedelta(days=1)
            elif time_range == 'week':
                start_date = end_date - timedelta(days=7)
            elif time_range == 'month':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)
            
            with self.db_manager.get_session() as db:
                # Get session analytics
                sessions = db.query(LearningSession).filter(
                    and_(
                        LearningSession.student_id == student_id,
                        LearningSession.started_at >= start_date
                    )
                ).all()
                
                # Get practice analytics
                practice_stats = db.query(
                    func.count(PracticeAnalytics.id).label('total'),
                    func.sum(func.cast(PracticeAnalytics.correct, Integer)).label('correct'),
                    func.avg(PracticeAnalytics.time_spent_seconds).label('avg_time')
                ).filter(
                    and_(
                        PracticeAnalytics.student_id == student_id,
                        PracticeAnalytics.timestamp >= start_date
                    )
                ).first()
                
                # Get topic analytics
                topics = db.query(TopicAnalytics).filter_by(
                    student_id=student_id
                ).order_by(desc(TopicAnalytics.last_accessed)).limit(10).all()
                
                # Get daily metrics
                daily_metrics = db.query(DailyMetrics).filter(
                    and_(
                        DailyMetrics.student_id == student_id,
                        DailyMetrics.date >= start_date
                    )
                ).order_by(DailyMetrics.date).all()
            
            # Compile analytics
            analytics = {
                'student_id': student_id,
                'time_range': time_range,
                'summary': {
                    'total_sessions': len(sessions),
                    'total_time_hours': sum(s.duration_minutes or 0 for s in sessions) / 60,
                    'practice_problems_attempted': practice_stats.total or 0,
                    'practice_problems_correct': practice_stats.correct or 0,
                    'practice_accuracy': (
                        (practice_stats.correct or 0) / (practice_stats.total or 1)
                        if practice_stats.total else 0
                    ),
                    'avg_problem_time_seconds': practice_stats.avg_time or 0
                },
                'sessions': [
                    {
                        'session_id': s.session_id,
                        'topic': s.topic,
                        'subject': s.subject,
                        'duration_minutes': s.duration_minutes,
                        'started_at': s.started_at.isoformat() if s.started_at else None
                    }
                    for s in sessions[-10:]  # Last 10 sessions
                ],
                'top_topics': [
                    {
                        'topic': t.topic,
                        'subject': t.subject,
                        'mastery_level': t.mastery_level,
                        'success_rate': t.success_rate,
                        'total_sessions': t.total_sessions,
                        'last_accessed': t.last_accessed.isoformat() if t.last_accessed else None
                    }
                    for t in topics
                ],
                'daily_progress': [
                    {
                        'date': d.date.isoformat() if d.date else None,
                        'sessions': d.sessions_count,
                        'time_minutes': d.total_time_minutes,
                        'accuracy': d.daily_accuracy,
                        'engagement': d.engagement_score
                    }
                    for d in daily_metrics
                ]
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting student analytics: {e}")
            return {'error': str(e)}
    
    def get_topic_performance(
        self,
        student_id: str,
        topic: str
    ) -> Dict[str, Any]:
        """Get detailed performance for a specific topic"""
        try:
            with self.db_manager.get_session() as db:
                # Get topic analytics
                topic_stats = db.query(TopicAnalytics).filter_by(
                    student_id=student_id,
                    topic=topic
                ).first()
                
                if not topic_stats:
                    return {
                        'topic': topic,
                        'message': 'No data available for this topic'
                    }
                
                # Get recent practice problems
                recent_practice = db.query(PracticeAnalytics).filter(
                    and_(
                        PracticeAnalytics.student_id == student_id,
                        PracticeAnalytics.topic == topic
                    )
                ).order_by(desc(PracticeAnalytics.timestamp)).limit(20).all()
                
                # Calculate trend
                if len(recent_practice) >= 5:
                    recent_5 = recent_practice[:5]
                    older_5 = recent_practice[5:10] if len(recent_practice) >= 10 else []
                    
                    recent_accuracy = sum(p.correct for p in recent_5) / len(recent_5)
                    older_accuracy = (
                        sum(p.correct for p in older_5) / len(older_5)
                        if older_5 else recent_accuracy
                    )
                    
                    trend = 'improving' if recent_accuracy > older_accuracy else (
                        'declining' if recent_accuracy < older_accuracy else 'stable'
                    )
                else:
                    trend = 'insufficient_data'
                
                performance = {
                    'topic': topic,
                    'subject': topic_stats.subject,
                    'mastery_level': topic_stats.mastery_level,
                    'total_sessions': topic_stats.total_sessions,
                    'total_time_hours': topic_stats.total_time_minutes / 60,
                    'practice_attempted': topic_stats.practice_attempted,
                    'practice_correct': topic_stats.practice_correct,
                    'success_rate': topic_stats.success_rate,
                    'trend': trend,
                    'recent_practice': [
                        {
                            'difficulty': p.difficulty,
                            'correct': p.correct,
                            'time_spent': p.time_spent_seconds,
                            'hints_used': p.hints_used,
                            'timestamp': p.timestamp.isoformat()
                        }
                        for p in recent_practice[:10]
                    ]
                }
                
                return performance
                
        except Exception as e:
            logger.error(f"Error getting topic performance: {e}")
            return {'error': str(e)}
    
    def get_learning_streaks(
        self,
        student_id: str
    ) -> Dict[str, Any]:
        """Get learning streak information for a student"""
        try:
            with self.db_manager.get_session() as db:
                # Get daily metrics for streak calculation
                daily_metrics = db.query(DailyMetrics).filter_by(
                    student_id=student_id
                ).order_by(desc(DailyMetrics.date)).limit(30).all()
                
                if not daily_metrics:
                    return {
                        'current_streak': 0,
                        'longest_streak': 0,
                        'total_active_days': 0
                    }
                
                # Calculate current streak
                current_streak = 0
                today = datetime.utcnow().date()
                
                for metric in daily_metrics:
                    if metric.is_active_day:
                        # Check if consecutive
                        expected_date = today - timedelta(days=current_streak)
                        if metric.date.date() == expected_date:
                            current_streak += 1
                        else:
                            break
                    else:
                        break
                
                # Calculate longest streak
                longest_streak = 0
                temp_streak = 0
                
                for i, metric in enumerate(reversed(daily_metrics)):
                    if metric.is_active_day:
                        if i == 0 or (
                            daily_metrics[-(i)].date.date() == 
                            daily_metrics[-(i+1)].date.date() + timedelta(days=1)
                        ):
                            temp_streak += 1
                            longest_streak = max(longest_streak, temp_streak)
                        else:
                            temp_streak = 1
                    else:
                        temp_streak = 0
                
                # Total active days
                total_active_days = sum(1 for m in daily_metrics if m.is_active_day)
                
                return {
                    'current_streak': current_streak,
                    'longest_streak': longest_streak,
                    'total_active_days': total_active_days,
                    'last_active': daily_metrics[0].date.isoformat() if daily_metrics else None
                }
                
        except Exception as e:
            logger.error(f"Error getting learning streaks: {e}")
            return {'error': str(e)}
    
    # ==================== Private Helper Methods ====================
    
    def _update_topic_analytics(
        self,
        student_id: str,
        topic: str,
        subject: str = None,
        practice_attempted: int = 0,
        practice_correct: int = 0,
        session_time_minutes: float = 0
    ) -> None:
        """Update topic-level analytics"""
        try:
            with self.db_manager.get_session() as db:
                # Get or create topic analytics
                topic_stats = db.query(TopicAnalytics).filter_by(
                    student_id=student_id,
                    topic=topic
                ).first()
                
                if not topic_stats:
                    topic_stats = TopicAnalytics(
                        student_id=student_id,
                        topic=topic,
                        subject=subject or 'general'
                    )
                    db.add(topic_stats)
                
                # Update metrics
                topic_stats.request_count += 1
                topic_stats.practice_attempted += practice_attempted
                topic_stats.practice_correct += practice_correct
                topic_stats.total_time_minutes += session_time_minutes
                topic_stats.last_accessed = datetime.utcnow()
                
                # Calculate rates
                if topic_stats.practice_attempted > 0:
                    topic_stats.success_rate = (
                        topic_stats.practice_correct / topic_stats.practice_attempted
                    )
                
                if topic_stats.total_sessions > 0:
                    topic_stats.avg_session_duration = (
                        topic_stats.total_time_minutes / topic_stats.total_sessions
                    )
                
                # Simple mastery calculation
                if topic_stats.practice_attempted >= 5:
                    topic_stats.mastery_level = min(
                        1.0,
                        topic_stats.success_rate * 0.7 + 
                        min(topic_stats.total_sessions / 10, 0.3)
                    )
                
                db.commit()
                
        except Exception as e:
            logger.error(f"Error updating topic analytics: {e}")
    
    def compute_daily_metrics(
        self,
        student_id: str,
        date: datetime = None
    ) -> None:
        """Compute and store daily metrics for a student (non-blocking)"""
        def _compute():
            try:
                if date is None:
                    target_date = datetime.utcnow().date()
                else:
                    target_date = date.date()
                
                start_of_day = datetime.combine(target_date, datetime.min.time())
                end_of_day = datetime.combine(target_date, datetime.max.time())
                
                with self.db_manager.get_session() as db:
                    # Get sessions for the day
                    sessions = db.query(LearningSession).filter(
                        and_(
                            LearningSession.student_id == student_id,
                            LearningSession.started_at >= start_of_day,
                            LearningSession.started_at <= end_of_day
                        )
                    ).all()
                    
                    if not sessions:
                        return
                    
                    # Get practice problems for the day
                    practice_stats = db.query(
                        func.count(PracticeAnalytics.id).label('total'),
                        func.sum(func.cast(PracticeAnalytics.correct, Integer)).label('correct')
                    ).filter(
                        and_(
                            PracticeAnalytics.student_id == student_id,
                            PracticeAnalytics.timestamp >= start_of_day,
                            PracticeAnalytics.timestamp <= end_of_day
                        )
                    ).first()
                    
                    # Collect topics and subjects
                    topics_studied = list(set(s.topic for s in sessions if s.topic))
                    subjects_studied = list(set(s.subject for s in sessions if s.subject))
                    
                    # Calculate metrics
                    total_time = sum(s.duration_minutes or 0 for s in sessions)
                    daily_accuracy = (
                        (practice_stats.correct or 0) / (practice_stats.total or 1)
                        if practice_stats.total else 0
                    )
                    
                    # Get or create daily metrics
                    daily_metric = db.query(DailyMetrics).filter_by(
                        student_id=student_id,
                        date=start_of_day
                    ).first()
                    
                    if not daily_metric:
                        daily_metric = DailyMetrics(
                            student_id=student_id,
                            date=start_of_day
                        )
                        db.add(daily_metric)
                    
                    # Update metrics
                    daily_metric.sessions_count = len(sessions)
                    daily_metric.total_time_minutes = total_time
                    daily_metric.topics_studied = topics_studied
                    daily_metric.subjects_studied = subjects_studied
                    daily_metric.practice_problems_attempted = practice_stats.total or 0
                    daily_metric.practice_problems_correct = practice_stats.correct or 0
                    daily_metric.daily_accuracy = daily_accuracy
                    daily_metric.is_active_day = len(sessions) > 0
                    
                    # Simple engagement calculation
                    if total_time > 0:
                        daily_metric.engagement_score = min(
                            1.0,
                            (len(sessions) / 5) * 0.3 +  # Session count factor
                            (total_time / 60) * 0.4 +     # Time factor (assuming 60 min is good)
                            daily_accuracy * 0.3           # Accuracy factor
                        )
                    
                    db.commit()
                    logger.info(f"Daily metrics computed for {student_id} on {target_date}")
                    
            except Exception as e:
                logger.error(f"Error computing daily metrics: {e}")
        
        # Execute in background thread (non-blocking)
        threading.Thread(target=_compute, daemon=True).start()


# Global instance
analytics_manager = AnalyticsManager()
