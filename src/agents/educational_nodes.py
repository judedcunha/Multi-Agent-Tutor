"""
Educational node implementations for LangGraph multi-agent system
Each node represents a specialized educational agent
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import hashlib
import json

from agents.state_schema import TutoringState, StudentProfile
from agents.ai_tutor import UniversalAITutor
from optimization.educational_caching import cache_manager
from optimization.cache_decorators import (
    cache_agent_response, 
    cache_lesson,
    cache_practice,
    cache_rag_search,
    cache_result
)

logger = logging.getLogger(__name__)


class EducationalNodes:
    """
    Collection of educational agent nodes for LangGraph
    Each method is a node that can be used in the tutoring graph
    LLM, Specialized Agents, and Advanced RAG
    """
    
    def __init__(
        self, 
        tutor: UniversalAITutor,
        llm_manager=None,
        specialized_agents=None,
        rag_system=None
    ):
        """
        Initialize with a tutor instance 
        
        Args:
            tutor: UniversalAITutor instance
            llm_manager: EducationalLLMManager for AI content 
            specialized_agents: Dict of specialized subject agents 
            rag_system: EducationalRAG for advanced retrieval 
        """
        self.tutor = tutor
        self.llm_manager = llm_manager
        self.specialized_agents = specialized_agents or {}
        self.rag_system = rag_system
        
        phase2_features = []
        if llm_manager:
            phase2_features.append("LLM")
        if specialized_agents:
            phase2_features.append("Specialized Agents")
        if rag_system:
            phase2_features.append("Advanced RAG")
        
        if phase2_features:
            logger.info(f"Educational nodes initialized with Phase 2: {', '.join(phase2_features)}")
        else:
            logger.info("Educational nodes initialized (Phase 1 only)")
    
    @cache_agent_response(ttl=3600)
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
    
    async def content_creator_node(self, state: TutoringState) -> TutoringState:
        """
        Content Creator Agent - Generates personalized educational content
        
        Creates comprehensive lesson plans and explanations tailored to the student
        Phase 2 of the project: Uses LLM for high-quality content when available
        automatic caching via decorators.
        """
        logger.info(f"Content Creator generating lesson for: {state['learning_request']}")
        
        try:
            topic = state['learning_request']
            subject = state['detected_subject']
            level = state['detected_level']
            student_profile = StudentProfile.from_dict(state['student_profile'])
            
            # Generate content (will be cached automatically by decorator)
            lesson_data = await self._generate_lesson_content(
                topic, subject, level, student_profile.learning_style
            )
            
            logger.info(f"Created lesson plan with {len(lesson_data['lesson_plan']['objectives'])} objectives")
            
            # Update state
            return {
                **state,
                'lesson_plan': lesson_data['lesson_plan'],
                'explanations': lesson_data['explanations'],
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
    
    @cache_lesson(ttl=3600)
    async def _generate_lesson_content(self, topic: str, subject: str, level: str, learning_style: str) -> Dict:
        """
        Internal method to generate lesson content with caching
        """
        # Generate lesson plan (Phase 1 - still useful for structure)
        lesson_plan = self.tutor.create_lesson_plan(
            topic=topic,
            subject=subject,
            level=level,
            learning_style=learning_style
        )
        
        # Generate detailed explanation
        # Phase 2: Use LLM if enabled, otherwise use rule-based
        if self.llm_manager:
            import asyncio
            import nest_asyncio
            
            # Enable nested event loops
            nest_asyncio.apply()
            
            try:
                # Run async LLM call properly
                loop = asyncio.get_event_loop()
                explanation_text = loop.run_until_complete(
                    self.llm_manager.create_lesson_explanation(
                        topic=topic,
                        level=level,
                        learning_style=learning_style,
                        student_context={
                            'prior_knowledge': [],
                            'level': level
                        }
                    )
                )
                
                explanation = {
                    'main_explanation': explanation_text,
                    'generated_by': 'llm',
                    'personalized': True
                }
                logger.info("Generated LLM-powered explanation")
                
            except Exception as e:
                logger.error(f"LLM explanation failed: {e}")
                raise RuntimeError(
                    f"Phase 2 LLM Manager is enabled but failed to generate content: {e}\n"
                    f"To fix: Check API keys, verify Ollama is running, or disable LLM features."
                )
        else:
            # Phase 1 mode - no LLM available
            explanation = self.tutor.generate_explanation(
                topic=topic,
                level=level,
                learning_style=learning_style
            )
            explanation['generated_by'] = 'rule-based'
        
        return {
            'lesson_plan': lesson_plan,
            'explanations': explanation
        }
    
    async def content_retriever_node(self, state: TutoringState) -> TutoringState:
        """
        Content Retriever Agent - Finds relevant educational resources
        
        Searches for and retrieves educational content from various sources
        Phase 2: Uses Advanced RAG when available
        automatic caching via decorators.
        """
        logger.info(f"Content Retriever searching for: {state['learning_request']}")
        
        try:
            topic = state['learning_request']
            subject = state['detected_subject']
            level = state['detected_level']
            
            # Retrieve content (will be cached automatically by decorator)
            educational_content = await self._retrieve_educational_content(
                topic, subject, level
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
    
    @cache_rag_search(ttl=1800)
    async def _retrieve_educational_content(self, query: str, subject: str, level: str) -> List[Dict]:
        """
        Internal method to retrieve educational content with caching
        """
        # Phase 2: Use Advanced RAG if available
        if self.rag_system and self.rag_system.initialized:
            import asyncio
            import nest_asyncio
            
            # Enable nested event loops
            nest_asyncio.apply()
            
            try:
                # Run async RAG search properly
                loop = asyncio.get_event_loop()
                educational_content = loop.run_until_complete(
                    self.rag_system.hybrid_search(
                        query=query,
                        subject=subject,
                        student_level=level,
                        top_k=5
                    )
                )
                
                # Format RAG results to match expected structure
                formatted_content = []
                for result in educational_content:
                    formatted_content.append({
                        'title': result.get('metadata', {}).get('title', query),
                        'content': result.get('content', ''),
                        'source': 'rag',
                        'relevance_score': result.get('combined_score', 0.5)
                    })
                
                educational_content = formatted_content
                logger.info(f"Retrieved {len(educational_content)} resources via Advanced RAG")
                
            except Exception as e:
                logger.error(f"RAG retrieval failed: {e}")
                raise RuntimeError(
                    f"Phase 2 RAG system is enabled but failed to retrieve content: {e}\n"
                    f"To fix: Check ChromaDB installation, verify data is indexed, or disable RAG features."
                )
        else:
            # Phase 1 mode - basic web search
            educational_content = self.tutor.find_educational_content(
                topic=query,
                subject=subject,
                level=level,
                max_results=5
            )
        
        return educational_content
    
    async def practice_generator_node(self, state: TutoringState) -> TutoringState:
        """
        Practice Generator Agent - Creates practice problems and exercises
        
        Generates appropriate practice problems based on the lesson content
        Phase 2: Uses LLM for more varied and appropriate problems
        automatic caching via decorators.
        """
        logger.info(f"📝 Practice Generator creating exercises for: {state['learning_request']}")
        
        try:
            topic = state['learning_request']
            subject = state['detected_subject']
            level = state['detected_level']
            
            # Generate problems (will be cached automatically by decorator)
            practice_problems = await self._generate_practice_problems(
                topic, subject, level, 5
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
    
    @cache_practice(ttl=1800)
    async def _generate_practice_problems(self, topic: str, subject: str, level: str, count: int) -> List[Dict]:
        """
        Internal method to generate practice problems with caching
        Note: The decorator expects (topic, level, count) signature
        """
        # Phase 2: Use LLM if available for better practice problems
        if self.llm_manager:
            import asyncio
            import nest_asyncio
            
            # Enable nested event loops
            nest_asyncio.apply()
            
            try:
                # Run async LLM call properly
                loop = asyncio.get_event_loop()
                practice_problems = loop.run_until_complete(
                    self.llm_manager.generate_practice_problems(
                        topic=topic,
                        level=level,
                        count=count,
                        difficulty_progression=True
                    )
                )
                
                logger.info(f"Created {len(practice_problems)} LLM-generated practice problems")
                
            except Exception as e:
                logger.error(f"LLM practice generation failed: {e}")
                raise RuntimeError(
                    f"Phase 2 LLM Manager is enabled but failed to generate practice problems: {e}\n"
                    f"To fix: Check API keys, verify Ollama is running, or disable LLM features."
                )
        else:
            # Phase 1 mode - rule-based problems
            practice_problems = self.tutor.create_practice_problems(
                topic=topic,
                subject=subject,
                level=level,
                count=count
            )
        
        return practice_problems
    
    @cache_agent_response(ttl=1800)
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
    
    @cache_agent_response(ttl=600)
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


def create_educational_nodes(
    tutor: UniversalAITutor,
    llm_manager=None,
    specialized_agents=None,
    rag_system=None
) -> EducationalNodes:
    """
    Factory function to create educational nodes
    
    Args:
        tutor: UniversalAITutor instance
        llm_manager: EducationalLLMManager for Phase 2 (optional)
        specialized_agents: Dict of specialized agents for Phase 2 (optional)
        rag_system: EducationalRAG for Phase 2 (optional)
        
    Returns:
        EducationalNodes instance with Phase 2 enhancements if provided
    """
    return EducationalNodes(
        tutor=tutor,
        llm_manager=llm_manager,
        specialized_agents=specialized_agents,
        rag_system=rag_system
    )
