"""
Multi-Agent Tutoring System using LangGraph
Main orchestration graph that coordinates all educational agents
"""

import logging
from typing import Dict, Any, Literal
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from agents.state_schema import TutoringState, StudentProfile, create_initial_state
from agents.educational_nodes import EducationalNodes, create_educational_nodes
from agents.ai_tutor import UniversalAITutor

logger = logging.getLogger(__name__)


class AdvancedTutoringSystem:
    """
    Advanced Multi-Agent Tutoring System
    
    Orchestrates specialized educational agents using LangGraph:
    1. SubjectExpertAgent - Detects subjects and routes appropriately
    2. ContentCreatorAgent - Generates personalized lesson plans
    3. ContentRetrieverAgent - Finds relevant educational resources
    4. PracticeGeneratorAgent - Creates adaptive practice problems
    5. AssessmentAgent - Evaluates student understanding
    6. ProgressTrackerAgent - Manages learning analytics
    
    Future agents (Phase 2+):
    - MathTutorAgent - Specialized mathematics education
    - ScienceTutorAgent - Specialized science education
    - ProgrammingTutorAgent - Specialized coding education
    - LearningAdapterAgent - Adapts to learning styles
    - VisualContentAgent - Creates educational visualizations
    """
    
    def __init__(self, use_local_model: bool = False):
        """
        Initialize the advanced tutoring system
        
        Args:
            use_local_model: Whether to use local models (for Phase 2)
        """
        self.use_local_model = use_local_model
        
        # Initialize the base tutor (preserves existing functionality)
        self.tutor = UniversalAITutor(use_local_model=use_local_model)
        
        # Create educational nodes
        self.nodes = create_educational_nodes(self.tutor)
        
        # Build the tutoring graph
        self.graph = self._create_tutoring_graph()
        
        # Compile the graph
        self.compiled_graph = self.graph.compile()
        
        logger.info("🎓 Advanced Tutoring System initialized with LangGraph")
    
    def _create_tutoring_graph(self) -> StateGraph:
        """
        Create the educational workflow graph
        
        This defines the multi-agent educational pipeline:
        START → Subject Expert → Content Creator → Content Retriever → 
        Practice Generator → Assessment Agent → Progress Tracker → END
        """
        # Create graph with TutoringState
        graph = StateGraph(TutoringState)
        
        # Add all educational agent nodes
        graph.add_node("subject_expert", self.nodes.subject_expert_node)
        graph.add_node("content_creator", self.nodes.content_creator_node)
        graph.add_node("content_retriever", self.nodes.content_retriever_node)
        graph.add_node("practice_generator", self.nodes.practice_generator_node)
        graph.add_node("assessment_agent", self.nodes.assessment_agent_node)
        graph.add_node("progress_tracker", self.nodes.progress_tracker_node)
        
        # Define the educational workflow
        # Start with subject expert
        graph.set_entry_point("subject_expert")
        
        # Linear educational pipeline (Phase 1)
        # Future: Add conditional routing based on subject/complexity (Phase 2)
        graph.add_edge("subject_expert", "content_creator")
        graph.add_edge("content_creator", "content_retriever")
        graph.add_edge("content_retriever", "practice_generator")
        graph.add_edge("practice_generator", "assessment_agent")
        graph.add_edge("assessment_agent", "progress_tracker")
        
        # End the workflow
        graph.add_edge("progress_tracker", END)
        
        logger.info("📊 Tutoring graph created with 6 educational agents")
        return graph
    
    def route_educational_request(self, state: TutoringState) -> Literal["subject_expert", "content_creator", "practice", "assessment"]:
        """
        Route educational requests to appropriate agents
        
        This is a placeholder for Phase 2 advanced routing.
        Currently, all requests start with subject_expert.
        
        Future routing logic:
        - Math problems → MathTutorAgent
        - Code questions → ProgrammingTutorAgent
        - Quick questions → Fast track
        - Complex topics → Full pipeline
        """
        # Phase 1: Simple routing - everyone starts at subject expert
        return "subject_expert"
    
    def teach_topic(
        self,
        topic: str,
        student_profile: StudentProfile = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Main teaching method using multi-agent system
        
        Args:
            topic: What the student wants to learn
            student_profile: Student's learning profile
            session_id: Optional session identifier
            
        Returns:
            Complete teaching session with all educational content
        """
        if student_profile is None:
            student_profile = StudentProfile()
        
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        logger.info(f"Starting multi-agent teaching session: {topic}")
        logger.info(f"Student: {student_profile.name} ({student_profile.level} level)")
        
        try:
            # Create initial state
            initial_state = create_initial_state(
                learning_request=topic,
                student_profile=student_profile,
                session_id=session_id
            )
            
            # Run the multi-agent graph
            logger.info("Executing multi-agent educational pipeline...")
            final_state = self.compiled_graph.invoke(initial_state)
            
            # Extract teaching session from final state
            teaching_session = self._compile_teaching_session(final_state, student_profile)
            
            logger.info(f"   Multi-agent session completed successfully")
            logger.info(f"   Agents involved: {len(final_state.get('agent_history', []))}")
            logger.info(f"   Errors: {len(final_state.get('errors', []))}")
            
            return teaching_session
            
        except Exception as e:
            logger.error(f" Multi-agent teaching failed: {e}")
            # Fallback to basic tutor if graph fails
            logger.warning("  Falling back to basic tutor...")
            return self.tutor.teach_topic(topic, student_profile)
    
    def _compile_teaching_session(
        self,
        state: TutoringState,
        student_profile: StudentProfile
    ) -> Dict[str, Any]:
        """
        Compile final teaching session from state
        
        Formats the state into a comprehensive teaching session response
        """
        teaching_session = {
            "topic": state['learning_request'],
            "student_profile": student_profile,
            "detected_subject": state.get('detected_subject', 'general'),
            "teaching_level": state.get('detected_level', student_profile.level),
            "timestamp": state.get('timestamp'),
            "session_id": state.get('session_id'),
            
            # Educational content
            "lesson_plan": state.get('lesson_plan', {}),
            "explanation": state.get('explanations', {}),
            "educational_content": state.get('educational_content', []),
            "practice_problems": state.get('practice_problems', []),
            "assessments": state.get('assessments', []),
            
            # Session metadata
            "learning_progress": state.get('learning_progress', {}),
            "session_feedback": state.get('session_feedback', {}),
            "visual_content": state.get('visual_content', []),
            
            # Agent orchestration details
            "multi_agent": True,
            "agents_involved": state.get('agent_history', []),
            "agent_count": len(state.get('agent_history', [])),
            "errors": state.get('errors', []),
            
            # Assessment readiness
            "assessment_ready": True,
            
            # Cost (Phase 1: still free)
            "cost": "0 - multi-agent orchestration active"
        }
        
        return teaching_session
    
    def get_graph_visualization(self) -> str:
        """
        Get ASCII visualization of the tutoring graph 
        
        Returns:
            String representation of the graph structure 
        """
        visualization = """
╔════════════════════════════════════════════════════════════════╗
║         MULTI-AGENT EDUCATIONAL TUTORING SYSTEM                ║
╚════════════════════════════════════════════════════════════════╝

                        [START]
                           │
                           ▼
                  ┌─────────────────┐
                  │ Subject Expert  │  🔍 Analyze & Route
                  └─────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Content Creator │  📚 Generate Lessons
                  └─────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │Content Retriever│  🔎 Find Resources
                  └─────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │Practice Generator│  📝 Create Exercises
                  └─────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │Assessment Agent │  📊 Evaluate Learning
                  └─────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │Progress Tracker │  📈 Track Progress
                  └─────────────────┘
                           │
                           ▼
                        [END]

Agents: 6 active | Status: Phase 1 Complete
Future: Math/Science/Programming specialists (Phase 2)
        """
        return visualization
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status and capabilities
        
        Returns:
            Dictionary with system information
        """
        return {
            "system": "Advanced Multi-Agent Tutoring System",
            "version": "1.0.0-phase1",
            "phase": "Phase 1: LangGraph Foundation",
            "status": "operational",
            "agents": {
                "active": [
                    "subject_expert",
                    "content_creator",
                    "content_retriever",
                    "practice_generator",
                    "assessment_agent",
                    "progress_tracker"
                ],
                "count": 6,
                "planned": [
                    "math_tutor_agent",
                    "science_tutor_agent",
                    "programming_tutor_agent",
                    "learning_adapter_agent",
                    "visual_content_agent"
                ]
            },
            "features": {
                "multi_agent_orchestration": True,
                "langgraph_integration": True,
                "subject_detection": True,
                "personalized_lessons": True,
                "practice_generation": True,
                "assessment_ready": True,
                "llm_integration": False,  # Phase 2
                "advanced_rag": False,  # Phase 2
                "streaming": False,  # Phase 3
                "database_persistence": False  # Phase 3
            },
            "capabilities": {
                "subjects": "all",
                "levels": ["beginner", "intermediate", "advanced"],
                "learning_styles": ["visual", "auditory", "kinesthetic", "mixed"]
            }
        }


def test_advanced_tutoring_system():
    """
    Test the advanced multi-agent tutoring system
    """
    print("\n" + "=" * 70)
    print("TESTING ADVANCED MULTI-AGENT TUTORING SYSTEM")
    print("=" * 70 + "\n")
    
    # Initialize system
    system = AdvancedTutoringSystem(use_local_model=False)
    
    # Show graph visualization
    print(system.get_graph_visualization())
    
    # Show system status
    print("\n📊 SYSTEM STATUS:")
    print("-" * 70)
    status = system.get_system_status()
    print(f"Version: {status['version']}")
    print(f"Phase: {status['phase']}")
    print(f"Active Agents: {status['agents']['count']}")
    print(f"Agent Names: {', '.join(status['agents']['active'])}")
    
    # Test teaching session
    print("\n\n🎓 TESTING TEACHING SESSION:")
    print("-" * 70)
    
    test_cases = [
        ("Python programming basics", StudentProfile(
            name="Alice",
            level="beginner",
            learning_style="visual"
        )),
        ("Calculus derivatives", StudentProfile(
            name="Bob",
            level="intermediate",
            learning_style="mixed"
        ))
    ]
    
    for topic, profile in test_cases[:1]:  # Test one for speed
        print(f"\n📖 Topic: {topic}")
        print(f" Student: {profile.name} ({profile.level} level, {profile.learning_style} style)")
        print("\n Running multi-agent pipeline...")
        
        session = system.teach_topic(topic, profile)
        
        print(f"\n Session completed!")
        print(f"   Subject: {session['detected_subject']}")
        print(f"   Level: {session['teaching_level']}")
        print(f"   Agents used: {session['agent_count']}")
        print(f"   Agent chain: {' → '.join(session['agents_involved'])}")
        print(f"   Lesson objectives: {len(session['lesson_plan'].get('objectives', []))}")
        print(f"   Educational resources: {len(session['educational_content'])}")
        print(f"   Practice problems: {len(session['practice_problems'])}")
        print(f"   Errors: {len(session['errors'])}")
        print(f"   Cost: {session['cost']}")
        
        # Show learning progress
        if session.get('learning_progress'):
            progress = session['learning_progress']
            print(f"\n Learning Progress:")
            print(f"   Status: {progress.get('completion_status', 'unknown')}")
            print(f"   Duration: {progress.get('session_duration', 'unknown')}")
            print(f"   Ready for learning: {progress.get('ready_for_learning', False)}")
    
    print("\n" + "=" * 70)
    print("TESTING COMPLETED SUCCESSFULLY!")
    print("=" * 70 + "\n")
    return True


if __name__ == "__main__":
    test_advanced_tutoring_system()
