"""
Educational node implementations for LangGraph multi-agent system
Each node represents a specialized educational agent
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from agents.state_schema import TutoringState, StudentProfile
from agents.ai_tutor import UniversalAITutor

logger = logging.getLogger(__name__)


class EducationalNodes:
    """
    Collection of educational agent nodes for LangGraph
    Each method is a node that can be used in the tutoring graph
    """
    
    def __init__(self, tutor: UniversalAITutor):
        """
        Initialize with a tutor instance for accessing existing functionality
        
        Args:
            tutor: UniversalAITutor instance
        """
        self.tutor = tutor
        logger.info("Educational nodes initialized")
    
    def subject_expert_node(self, state: TutoringState) -> TutoringState:
        """
        Subject Expert Agent - Detects subject and determines learning path
        
        This is the first agent that analyzes the learning request and routes
        to appropriate specialized agents.
        """
        logger.info(f"Subject Expert analyzing: {state['learning_request']}")
        
        try:
            # Use existing subject detection
            topic_analysis = self.tutor.detect_subject_and_level(state['learning_request'])
            
            # Enhance with additional educational metadata
            detected_subject = topic_analysis['subject']
            detected_level = topic_analysis['level']
            confidence = topic_analysis['confidence']
            
            # Use student's preferred level if higher confidence
            student_level = state['student_profile']['level']
            if confidence < 2 and student_level != "beginner":
                detected_level = student_level
            
            logger.info(f"Detected: {detected_subject} at {detected_level} level (confidence: {confidence})")
            
            # Update state
            return {
                **state,
                'detected_subject': detected_subject,
                'detected_level': detected_level,
                'subject_confidence': float(confidence),
                'current_agent': 'subject_expert',
                'next_agent': 'content_creator',  # Route to content creation
                'agent_history': state.get('agent_history', []) + ['subject_expert'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Subject expert error: {e}")
            return {
                **state,
                'errors': state.get('errors', []) + [f"subject_expert: {str(e)}"],
                'detected_subject': 'general',
                'detected_level': state['student_profile']['level'],
                'next_agent': 'content_creator'
            }
    
    def content_creator_node(self, state: TutoringState) -> TutoringState:
        """
        Content Creator Agent - Generates personalized educational content
        
        Creates comprehensive lesson plans and explanations tailored to the student
        """
        logger.info(f"Content Creator generating lesson for: {state['learning_request']}")
        
        try:
            topic = state['learning_request']
            subject = state['detected_subject']
            level = state['detected_level']
            student_profile = StudentProfile.from_dict(state['student_profile'])
            
            # Generate lesson plan
            lesson_plan = self.tutor.create_lesson_plan(
                topic=topic,
                subject=subject,
                level=level,
                learning_style=student_profile.learning_style
            )
            
            # Generate detailed explanation
            explanation = self.tutor.generate_explanation(
                topic=topic,
                level=level,
                learning_style=student_profile.learning_style
            )
            
            logger.info(f"Created lesson plan with {len(lesson_plan['objectives'])} objectives")
            
            # Update state
            return {
                **state,
                'lesson_plan': lesson_plan,
                'explanations': explanation,
                'current_agent': 'content_creator',
                'next_agent': 'content_retriever',
                'agent_history': state.get('agent_history', []) + ['content_creator'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Content creator error: {e}")
            return {
                **state,
                'errors': state.get('errors', []) + [f"content_creator: {str(e)}"],
                'next_agent': 'content_retriever'
            }
    
    def content_retriever_node(self, state: TutoringState) -> TutoringState:
        """
        Content Retriever Agent - Finds relevant educational resources
        
        Searches for and retrieves educational content from various sources
        """
        logger.info(f"Content Retriever searching for: {state['learning_request']}")
        
        try:
            topic = state['learning_request']
            subject = state['detected_subject']
            level = state['detected_level']
            
            # Retrieve educational content
            educational_content = self.tutor.find_educational_content(
                topic=topic,
                subject=subject,
                level=level,
                max_results=5
            )
            
            logger.info(f"Retrieved {len(educational_content)} educational resources")
            
            # Update state
            return {
                **state,
                'educational_content': educational_content,
                'current_agent': 'content_retriever',
                'next_agent': 'practice_generator',
                'agent_history': state.get('agent_history', []) + ['content_retriever'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Content retriever error: {e}")
            return {
                **state,
                'errors': state.get('errors', []) + [f"content_retriever: {str(e)}"],
                'educational_content': [],
                'next_agent': 'practice_generator'
            }
    
    def practice_generator_node(self, state: TutoringState) -> TutoringState:
        """
        Practice Generator Agent - Creates practice problems and exercises
        
        Generates appropriate practice problems based on the lesson content
        """
        logger.info(f"📝 Practice Generator creating exercises for: {state['learning_request']}")
        
        try:
            topic = state['learning_request']
            subject = state['detected_subject']
            level = state['detected_level']
            
            # Generate practice problems
            practice_problems = self.tutor.create_practice_problems(
                topic=topic,
                subject=subject,
                level=level,
                count=5
            )
            
            logger.info(f"Created {len(practice_problems)} practice problems")
            
            # Update state
            return {
                **state,
                'practice_problems': practice_problems,
                'current_agent': 'practice_generator',
                'next_agent': 'assessment_agent',
                'agent_history': state.get('agent_history', []) + ['practice_generator'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Practice generator error: {e}")
            return {
                **state,
                'errors': state.get('errors', []) + [f"practice_generator: {str(e)}"],
                'practice_problems': [],
                'next_agent': 'assessment_agent'
            }
    
    def assessment_agent_node(self, state: TutoringState) -> TutoringState:
        """
        Assessment Agent - Prepares assessment strategy
        
        Creates assessment plan for measuring student understanding
        """
        logger.info(f"Assessment Agent preparing evaluation for: {state['learning_request']}")
        
        try:
            topic = state['learning_request']
            level = state['detected_level']
            
            # Create assessment plan
            assessment_plan = {
                'topic': topic,
                'level': level,
                'assessment_ready': True,
                'assessment_types': ['formative', 'practice_based'],
                'evaluation_criteria': [
                    'Understanding of key concepts',
                    'Ability to apply knowledge',
                    'Problem-solving skills',
                    'Retention and recall'
                ],
                'recommended_practice_count': len(state.get('practice_problems', [])),
                'mastery_threshold': 0.7 if level == 'beginner' else 0.8
            }
            
            logger.info(f"Assessment plan ready with {len(assessment_plan['evaluation_criteria'])} criteria")
            
            # Update state
            return {
                **state,
                'assessments': [assessment_plan],
                'current_agent': 'assessment_agent',
                'next_agent': 'progress_tracker',
                'agent_history': state.get('agent_history', []) + ['assessment_agent'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Assessment agent error: {e}")
            return {
                **state,
                'errors': state.get('errors', []) + [f"assessment_agent: {str(e)}"],
                'next_agent': 'progress_tracker'
            }
    
    def progress_tracker_node(self, state: TutoringState) -> TutoringState:
        """
        Progress Tracker Agent - Tracks and reports learning progress
        
        Final agent that compiles all learning data and prepares session summary
        """
        logger.info(f"Progress Tracker compiling session for: {state['learning_request']}")
        
        try:
            # Compile learning progress
            learning_progress = {
                'topic': state['learning_request'],
                'subject': state['detected_subject'],
                'level': state['detected_level'],
                'session_duration': self._calculate_session_duration(state),
                'agents_involved': state.get('agent_history', []),
                'content_created': {
                    'lesson_plan': bool(state.get('lesson_plan')),
                    'explanations': bool(state.get('explanations')),
                    'educational_content': len(state.get('educational_content', [])),
                    'practice_problems': len(state.get('practice_problems', [])),
                    'assessments': len(state.get('assessments', []))
                },
                'completion_status': 'completed',
                'errors_encountered': len(state.get('errors', [])),
                'ready_for_learning': True
            }
            
            # Create session feedback
            session_feedback = {
                'overall_quality': 'high' if len(state.get('errors', [])) == 0 else 'good',
                'content_comprehensiveness': self._evaluate_completeness(state),
                'recommendations': self._generate_recommendations(state),
                'next_steps': [
                    f"Review the lesson plan for {state['learning_request']}",
                    "Work through the practice problems",
                    "Ask questions on any unclear concepts",
                    "Complete self-assessment"
                ]
            }
            
            logger.info(f"Session completed successfully - {len(state.get('agent_history', []))} agents involved")
            
            # Update state
            return {
                **state,
                'learning_progress': learning_progress,
                'session_feedback': session_feedback,
                'current_agent': 'progress_tracker',
                'next_agent': 'end',
                'agent_history': state.get('agent_history', []) + ['progress_tracker'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Progress tracker error: {e}")
            return {
                **state,
                'errors': state.get('errors', []) + [f"progress_tracker: {str(e)}"],
                'next_agent': 'end'
            }
    
    def _calculate_session_duration(self, state: TutoringState) -> str:
        """Calculate session duration"""
        try:
            from datetime import datetime
            start = datetime.fromisoformat(state['session_start'])
            end = datetime.fromisoformat(state['timestamp'])
            duration = (end - start).total_seconds()
            return f"{duration:.2f} seconds"
        except:
            return "unknown"
    
    def _evaluate_completeness(self, state: TutoringState) -> str:
        """Evaluate content completeness"""
        components = [
            state.get('lesson_plan'),
            state.get('explanations'),
            state.get('educational_content'),
            state.get('practice_problems')
        ]
        complete_count = sum(1 for c in components if c)
        
        if complete_count == len(components):
            return "comprehensive"
        elif complete_count >= len(components) * 0.75:
            return "good"
        else:
            return "partial"
    
    def _generate_recommendations(self, state: TutoringState) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Check for errors
        if state.get('errors'):
            recommendations.append("Some agents encountered issues - consider retrying for better results")
        
        # Check content quality
        if not state.get('educational_content'):
            recommendations.append("Try rephrasing your learning request for better content retrieval")
        
        # Level-specific recommendations
        level = state['detected_level']
        if level == 'beginner':
            recommendations.append("Take your time with each concept before moving forward")
        elif level == 'advanced':
            recommendations.append("Explore additional resources for deeper understanding")
        
        if not recommendations:
            recommendations.append("Excellent session - all educational content generated successfully")
        
        return recommendations


def create_educational_nodes(tutor: UniversalAITutor) -> EducationalNodes:
    """
    Factory function to create educational nodes
    
    Args:
        tutor: UniversalAITutor instance
        
    Returns:
        EducationalNodes instance
    """
    return EducationalNodes(tutor)
