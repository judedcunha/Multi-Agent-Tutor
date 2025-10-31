"""
LangSmith integration for production monitoring and tracing
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from functools import wraps

from langsmith import Client
from langsmith.run_helpers import traceable

logger = logging.getLogger(__name__)

# Try different import paths for LangChainTracer (depends on langchain version)
LangChainTracer = None
try:
    from langchain_core.tracers import LangChainTracer
    logger.debug("Imported LangChainTracer from langchain_core")
except ImportError:
    try:
        from langchain.callbacks.tracers import LangChainTracer
        logger.debug("Imported LangChainTracer from langchain.callbacks")
    except ImportError:
        try:
            from langchain_community.callbacks.tracers import LangChainTracer
            logger.debug("Imported LangChainTracer from langchain_community")
        except ImportError:
            logger.warning("Could not import LangChainTracer - callbacks will be disabled")
            LangChainTracer = None


class LangSmithMonitor:
    """Monitors educational agents with LangSmith tracing and evaluation"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.tracer: Optional[LangChainTracer] = None
        self.project_name = "multi-agent-tutor"
        self.enabled = False
        
    def initialize(self):
        """Initialize LangSmith client and tracer"""
        # Check if monitoring is enabled
        enabled = os.getenv('ENABLE_LANGSMITH_TRACING', 'false').lower() == 'true'
        if not enabled:
            logger.info("LangSmith tracing is disabled")
            return False
        
        # Get API key
        api_key = os.getenv('LANGSMITH_API_KEY')
        if not api_key:
            logger.warning("LangSmith API key not found - monitoring disabled")
            return False
        
        # Get project name from env or use default
        self.project_name = os.getenv('LANGSMITH_PROJECT', 'multi-agent-tutor')
        
        try:
            # Initialize client
            self.client = Client(api_key=api_key)
            
            # Initialize tracer for LangChain integration (if available)
            if LangChainTracer is not None:
                self.tracer = LangChainTracer(
                    project_name=self.project_name,
                    client=self.client
                )
                logger.info(f"LangChain tracer initialized for project: {self.project_name}")
            else:
                self.tracer = None
                logger.warning("LangChain tracer not available - using direct client only")
            
            self.enabled = True
            logger.info(f"LangSmith monitoring initialized for project: {self.project_name}")
            return True
            
        except Exception as e:
            logger.error(f"LangSmith initialization failed: {e}")
            self.enabled = False
            return False
    
    def get_tracer(self) -> Optional[LangChainTracer]:
        """Get LangChain tracer for callbacks"""
        return self.tracer if self.enabled else None
    
    def is_enabled(self) -> bool:
        """Check if monitoring is enabled"""
        return self.enabled
    
    # ============ Session Tracking ============
    
    def start_teaching_session(
        self, 
        topic: str, 
        student_profile: Dict[str, Any],
        session_id: str
    ) -> Optional[str]:
        """
        Start tracking a teaching session
        
        Args:
            topic: What's being taught
            student_profile: Student information
            session_id: Unique session identifier
            
        Returns:
            Run ID for tracking, or None if disabled
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            # Create a run for the entire teaching session
            run = self.client.create_run(
                name=f"teaching_session",
                run_type="chain",
                inputs={
                    "topic": topic,
                    "student_name": student_profile.get("name", "Student"),
                    "level": student_profile.get("level", "beginner"),
                    "learning_style": student_profile.get("learning_style", "mixed"),
                    "session_id": session_id
                },
                start_time=datetime.utcnow(),
                project_name=self.project_name,
                tags=["teaching", "multi-agent", f"level:{student_profile.get('level', 'unknown')}"],
                extra={
                    "session_id": session_id,
                    "session_type": "teaching"
                }
            )
            
            # Get run ID - handle different return types
            if run is None:
                logger.warning("create_run returned None")
                return None
            
            # Check if it's a Run object with id attribute
            if hasattr(run, 'id'):
                run_id = str(run.id)
            # Or if it's a dict
            elif isinstance(run, dict) and 'id' in run:
                run_id = str(run['id'])
            else:
                logger.warning(f"Unexpected run type: {type(run)}")
                return None
            
            logger.info(f"Started LangSmith tracking for session: {session_id}")
            return run_id
            
        except Exception as e:
            logger.error(f"Error starting session tracking: {e}")
            return None
    
    def end_teaching_session(
        self,
        run_id: str,
        outputs: Dict[str, Any],
        success: bool = True
    ):
        """
        Complete teaching session tracking
        
        Args:
            run_id: The run ID from start_teaching_session
            outputs: Session results
            success: Whether session completed successfully
        """
        if not self.enabled or not self.client or not run_id:
            return
        
        try:
            # Update the run with outputs
            self.client.update_run(
                run_id=run_id,
                outputs=outputs,
                end_time=datetime.utcnow(),
                error=None if success else "Session failed"
            )
            
            logger.info(f"Completed LangSmith tracking for run: {run_id}")
            
        except Exception as e:
            logger.error(f"Error ending session tracking: {e}")
    
    # ============ Agent Execution Tracking ============
    
    def track_agent_execution(
        self,
        parent_run_id: Optional[str],
        agent_name: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        duration_ms: int,
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        Track individual agent execution
        
        Args:
            parent_run_id: Parent teaching session run ID
            agent_name: Name of the agent (e.g., 'subject_expert')
            inputs: Agent inputs
            outputs: Agent outputs
            duration_ms: Execution duration in milliseconds
            success: Whether execution succeeded
            error: Error message if failed
        """
        if not self.enabled or not self.client:
            return
        
        try:
            # Determine run type based on agent
            run_type = "llm" if any(x in agent_name.lower() for x in ["llm", "gpt", "chat"]) else "tool"
            
            # Create child run for this agent
            run_data = {
                "name": f"agent_{agent_name}",
                "run_type": run_type,
                "inputs": inputs,
                "outputs": outputs,
                "project_name": self.project_name,
                "tags": ["agent", agent_name],
                "extra": {
                    "agent_type": agent_name,
                    "duration_ms": duration_ms,
                    "success": success
                }
            }
            
            # Add parent if available
            if parent_run_id:
                run_data["parent_run_id"] = parent_run_id
            
            # Add error if failed
            if not success and error:
                run_data["error"] = error
            
            self.client.create_run(**run_data)
            
        except Exception as e:
            logger.error(f"Error tracking agent execution: {e}")
    
    # ============ Quality Evaluation ============
    
    def evaluate_teaching_session(
        self,
        session_data: Dict[str, Any],
        run_id: Optional[str] = None
    ) -> Optional[Dict[str, float]]:
        """
        Evaluate teaching session quality
        
        Args:
            session_data: Complete session data
            run_id: Optional run ID to attach evaluation to
            
        Returns:
            Dictionary of scores, or None if disabled
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            # Calculate quality scores
            scores = {
                "content_completeness": self._score_content_completeness(session_data),
                "personalization_quality": self._score_personalization(session_data),
                "engagement_level": self._score_engagement(session_data),
                "educational_value": self._score_educational_value(session_data),
                "overall_quality": 0.0  # Will be calculated
            }
            
            # Calculate overall score
            scores["overall_quality"] = sum(scores.values()) / (len(scores) - 1)
            
            # Attach to run if run_id provided
            if run_id:
                self.client.create_feedback(
                    run_id=run_id,
                    key="teaching_quality",
                    score=scores["overall_quality"],
                    value="auto_evaluation",
                    comment=f"Scores: {scores}"
                )
            
            logger.info(f"Session evaluation - Overall quality: {scores['overall_quality']:.2f}")
            return scores
            
        except Exception as e:
            logger.error(f"Error evaluating session: {e}")
            return None
    
    def _score_content_completeness(self, session_data: Dict[str, Any]) -> float:
        """Score whether all expected content was generated"""
        score = 0.0
        
        # Check for lesson plan
        if session_data.get("lesson_plan") and session_data["lesson_plan"].get("objectives"):
            score += 0.25
        
        # Check for explanations
        if session_data.get("explanations") and session_data["explanations"].get("main_explanation"):
            score += 0.25
        
        # Check for practice problems
        if session_data.get("practice_problems") and len(session_data["practice_problems"]) > 0:
            score += 0.25
        
        # Check for resources
        if session_data.get("educational_content") and len(session_data["educational_content"]) > 0:
            score += 0.25
        
        return score
    
    def _score_personalization(self, session_data: Dict[str, Any]) -> float:
        """Score how well content was personalized"""
        score = 0.5  # Base score
        
        student_profile = session_data.get("student_profile", {})
        
        # Check if level was used
        detected_level = session_data.get("detected_level", "").lower()
        profile_level = student_profile.get("level", "").lower()
        if detected_level and detected_level == profile_level:
            score += 0.25
        
        # Check if learning style was considered
        learning_style = student_profile.get("learning_style", "")
        explanations = str(session_data.get("explanations", {}))
        if learning_style and learning_style.lower() in explanations.lower():
            score += 0.25
        
        return min(score, 1.0)
    
    def _score_engagement(self, session_data: Dict[str, Any]) -> float:
        """Estimate engagement level"""
        score = 0.5  # Base score
        
        # Good session duration (10-45 minutes is ideal)
        duration = session_data.get("duration_minutes", 0)
        if 10 <= duration <= 45:
            score += 0.25
        
        # Session completed
        if session_data.get("completed", False):
            score += 0.25
        
        return min(score, 1.0)
    
    def _score_educational_value(self, session_data: Dict[str, Any]) -> float:
        """Score the educational value"""
        score = 0.0
        
        # Quality lesson objectives
        lesson = session_data.get("lesson_plan", {})
        objectives = lesson.get("objectives", [])
        if len(objectives) >= 3:
            score += 0.3
        
        # Good number of practice problems
        problems = session_data.get("practice_problems", [])
        if len(problems) >= 3:
            score += 0.3
        
        # Multiple agent coordination
        agents = session_data.get("agents_involved", [])
        if len(agents) >= 4:
            score += 0.2
        
        # Has assessment strategy
        if session_data.get("assessments"):
            score += 0.2
        
        return min(score, 1.0)
    
    # ============ Performance Monitoring ============
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a performance metric
        
        Args:
            metric_name: Name of metric (e.g., 'response_time_ms')
            value: Metric value
            metadata: Additional context
        """
        if not self.enabled:
            return
        
        try:
            # Log to LangSmith as a run
            self.client.create_run(
                name=f"metric_{metric_name}",
                run_type="chain",
                inputs={"metric_name": metric_name},
                outputs={"value": value, "metadata": metadata or {}},
                project_name=self.project_name,
                tags=["metric", metric_name]
            )
        except Exception as e:
            logger.error(f"Error logging metric: {e}")
    
    def get_project_stats(self) -> Optional[Dict[str, Any]]:
        """Get statistics about the project"""
        if not self.enabled or not self.client:
            return None
        
        try:
            # Note: This requires LangSmith API access
            # Basic stats that we can track
            return {
                "project_name": self.project_name,
                "enabled": self.enabled,
                "message": "Use LangSmith UI for detailed statistics"
            }
        except Exception as e:
            logger.error(f"Error getting project stats: {e}")
            return None


# ============ Decorator for Easy Tracing ============

def trace_agent(agent_name: str):
    """
    Decorator to automatically trace agent execution
    
    Usage:
        @trace_agent("subject_expert")
        async def subject_expert_node(state: TutoringState):
            # Your agent code
            return state
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get monitor instance
            monitor = langsmith_monitor
            
            if not monitor.is_enabled():
                # If not enabled, just run the function
                return await func(*args, **kwargs)
            
            # Extract state if available
            state = args[0] if args else kwargs.get('state')
            session_id = state.get('session_id') if isinstance(state, dict) else None
            
            # Start timing
            start_time = datetime.utcnow()
            
            try:
                # Execute function
                result = await func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                # Track execution
                monitor.track_agent_execution(
                    parent_run_id=session_id,
                    agent_name=agent_name,
                    inputs={"state_keys": list(state.keys()) if isinstance(state, dict) else []},
                    outputs={"success": True},
                    duration_ms=duration_ms,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # Calculate duration
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                # Track failure
                monitor.track_agent_execution(
                    parent_run_id=session_id,
                    agent_name=agent_name,
                    inputs={"state_keys": list(state.keys()) if isinstance(state, dict) else []},
                    outputs={"error": str(e)},
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e)
                )
                
                raise
        
        return wrapper
    return decorator


# Global monitor instance
langsmith_monitor = LangSmithMonitor()


# ============ Helper Functions ============

def initialize_monitoring() -> bool:
    """Initialize LangSmith monitoring globally"""
    return langsmith_monitor.initialize()


def get_monitor() -> LangSmithMonitor:
    """Get the global monitor instance"""
    return langsmith_monitor


def get_tracer() -> Optional[LangChainTracer]:
    """Get LangChain tracer for callbacks"""
    return langsmith_monitor.get_tracer()
