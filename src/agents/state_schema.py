"""
State management schema for multi-agent tutoring system
Defines the shared state structure used across all agents
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


@dataclass
class StudentProfile:
    """Enhanced student profile with comprehensive learning data"""
    name: str = "Student"
    level: str = "beginner"  # beginner, intermediate, advanced
    learning_style: str = "mixed"  # visual, auditory, kinesthetic, mixed
    subjects_mastered: List[str] = field(default_factory=list)
    learning_goals: List[str] = field(default_factory=list)
    current_topic: str = ""
    progress_scores: Dict[str, float] = field(default_factory=dict)
    session_history: List[Dict] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "level": self.level,
            "learning_style": self.learning_style,
            "subjects_mastered": self.subjects_mastered,
            "learning_goals": self.learning_goals,
            "current_topic": self.current_topic,
            "progress_scores": self.progress_scores,
            "session_history": self.session_history,
            "preferences": self.preferences
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudentProfile':
        """Create from dictionary"""
        return cls(
            name=data.get("name", "Student"),
            level=data.get("level", "beginner"),
            learning_style=data.get("learning_style", "mixed"),
            subjects_mastered=data.get("subjects_mastered", []),
            learning_goals=data.get("learning_goals", []),
            current_topic=data.get("current_topic", ""),
            progress_scores=data.get("progress_scores", {}),
            session_history=data.get("session_history", []),
            preferences=data.get("preferences", {})
        )


class TutoringState(TypedDict):
    """
    Comprehensive state for multi-agent tutoring system
    This state is passed between all agents in the LangGraph
    """
    # Communication and messages
    messages: List[BaseMessage]
    
    # Learning request and context
    learning_request: str
    student_profile: Dict[str, Any]  # Serialized StudentProfile
    
    # Subject detection and routing
    detected_subject: str
    detected_level: str
    subject_confidence: float
    
    # Educational content
    educational_content: List[Dict[str, Any]]
    
    # Lesson planning
    lesson_plan: Dict[str, Any]
    
    # Explanations and teaching
    explanations: Dict[str, Any]
    
    # Practice and exercises
    practice_problems: List[Dict[str, Any]]
    
    # Assessment data
    assessments: List[Dict[str, Any]]
    
    # Agent orchestration
    current_agent: str
    next_agent: str
    agent_history: List[str]
    
    # Learning progress
    learning_progress: Dict[str, Any]
    
    # Session feedback
    session_feedback: Dict[str, Any]
    
    # Visual content
    visual_content: List[Dict[str, Any]]
    
    # Session management
    session_id: Optional[str]
    
    # Streaming manager (for Phase 3)
    streaming_manager: Optional[Any]
    
    # Error handling
    errors: List[str]
    
    # Metadata
    timestamp: str
    session_start: str


def create_initial_state(
    learning_request: str,
    student_profile: StudentProfile,
    session_id: Optional[str] = None
) -> TutoringState:
    """
    Create initial state for a tutoring session
    
    Args:
        learning_request: What the student wants to learn
        student_profile: Student's learning profile
        session_id: Optional session identifier
        
    Returns:
        Initial TutoringState
    """
    from datetime import datetime
    
    return TutoringState(
        messages=[],
        learning_request=learning_request,
        student_profile=student_profile.to_dict(),
        detected_subject="",
        detected_level=student_profile.level,
        subject_confidence=0.0,
        educational_content=[],
        lesson_plan={},
        explanations={},
        practice_problems=[],
        assessments=[],
        current_agent="start",
        next_agent="subject_expert",
        agent_history=[],
        learning_progress={},
        session_feedback={},
        visual_content=[],
        session_id=session_id,
        streaming_manager=None,
        errors=[],
        timestamp=datetime.now().isoformat(),
        session_start=datetime.now().isoformat()
    )


def update_state_with_agent(
    state: TutoringState,
    agent_name: str,
    updates: Dict[str, Any]
) -> TutoringState:
    """
    Update state with results from an agent
    
    Args:
        state: Current tutoring state
        agent_name: Name of agent making updates
        updates: Dictionary of updates to apply
        
    Returns:
        Updated TutoringState
    """
    from datetime import datetime
    
    # Update agent history
    agent_history = state.get("agent_history", [])
    agent_history.append(agent_name)
    
    # Apply updates
    updated_state = {**state, **updates}
    updated_state["agent_history"] = agent_history
    updated_state["current_agent"] = agent_name
    updated_state["timestamp"] = datetime.now().isoformat()
    
    return updated_state
