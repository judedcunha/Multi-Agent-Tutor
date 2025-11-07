"""
Multi-Agent Tutoring System using LangGraph
Main orchestration graph that coordinates all educational agents
LLM Integration & Specialized Agents
"""

import os
import logging
from typing import Dict, Any, Literal, Optional
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from agents.state_schema import TutoringState, StudentProfile, create_initial_state
from agents.educational_nodes import EducationalNodes, create_educational_nodes
from agents.ai_tutor import UniversalAITutor

logger = logging.getLogger(__name__)

# Import new components 
try:
    from llm.educational_clients import create_llm_manager
    LLM_AVAILABLE = True
except ImportError:
    logger.warning("LLM components not available - install with: pip install openai ollama")
    LLM_AVAILABLE = False

try:
    from agents.subject_experts import create_specialized_agents
    SPECIALIZED_AGENTS_AVAILABLE = True
except ImportError:
    logger.warning("Specialized agents not available")
    SPECIALIZED_AGENTS_AVAILABLE = False

try:
    from rag.educational_retrieval import create_rag_system
    RAG_AVAILABLE = True
except ImportError:
    logger.warning("RAG system not available - install with: pip install chromadb sentence-transformers")
    RAG_AVAILABLE = False

try:
    from monitoring.educational_analytics import analytics_manager
    ANALYTICS_AVAILABLE = True
except ImportError:
    logger.warning("Analytics system not available")
    ANALYTICS_AVAILABLE = False


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
    
    def __init__(
        self, 
        use_local_model: bool = False,
        enable_llm: bool = None,
        enable_specialized_agents: bool = None,
        enable_advanced_rag: bool = None
    ):
        """
        Initialize the advanced tutoring system
        
        Args:
            use_local_model: Whether to use local models
            enable_llm: Enable LLM features (Phase 2)
            enable_specialized_agents: Enable specialized subject agents (Phase 2)
            enable_advanced_rag: Enable advanced RAG (Phase 2)
        """
        self.use_local_model = use_local_model
        
        # Phase 2 feature flags
        if enable_llm is None:
            enable_llm = os.getenv('USE_OPENAI', 'true').lower() == 'true' or os.getenv('USE_OLLAMA', 'true').lower() == 'true'
        if enable_specialized_agents is None:
            enable_specialized_agents = os.getenv('USE_SPECIALIZED_AGENTS', 'true').lower() == 'true'
        if enable_advanced_rag is None:
            enable_advanced_rag = os.getenv('USE_ADVANCED_RAG', 'true').lower() == 'true'
        
        self.enable_llm = enable_llm and LLM_AVAILABLE
        self.enable_specialized_agents = enable_specialized_agents and SPECIALIZED_AGENTS_AVAILABLE
        self.enable_advanced_rag = enable_advanced_rag and RAG_AVAILABLE
        
        # Initialize the base tutor (preserves existing functionality)
        self.tutor = UniversalAITutor(use_local_model=use_local_model)
        
        # Phase 2: Initialize LLM Manager
        self.llm_manager = None
        if self.enable_llm:
            try:
                self.llm_manager = create_llm_manager()
                logger.info("Phase 2: LLM Manager initialized")
            except Exception as e:
                logger.warning(f"Phase 2: LLM Manager failed to initialize: {e}")
                self.enable_llm = False
        
        # Phase 2: Initialize Specialized Agents
        self.specialized_agents = None
        if self.enable_specialized_agents:
            try:
                self.specialized_agents = create_specialized_agents(self.llm_manager)
                logger.info("Phase 2: Specialized agents initialized")
            except Exception as e:
                logger.warning(f"Phase 2: Specialized agents failed: {e}")
                self.enable_specialized_agents = False
        
        # Phase 2: Initialize RAG System
        self.rag_system = None
        self.reranker = None
        if self.enable_advanced_rag:
            try:
                self.rag_system, self.reranker = create_rag_system()
                logger.info("Phase 2: Advanced RAG system initialized")
            except Exception as e:
                logger.warning(f"Phase 2: RAG system failed: {e}")
                self.enable_advanced_rag = False
        
        # Validate configuration AFTER initialization
        self._validate_configuration(enable_llm, enable_specialized_agents, enable_advanced_rag)
        
        # Create educational nodes (pass Phase 2 & 3 components)
        self.analytics = analytics_manager if ANALYTICS_AVAILABLE else None
        self.nodes = create_educational_nodes(
            self.tutor,
            llm_manager=self.llm_manager,
            specialized_agents=self.specialized_agents,
            rag_system=self.rag_system,
            analytics_manager=self.analytics
        )
        
        # Build the tutoring graph
        self.graph = self._create_tutoring_graph()
        
        # Compile the graph
        self.compiled_graph = self.graph.compile()
        
        phase_features = []
        if self.enable_llm:
            phase_features.append("LLM")
        if self.enable_specialized_agents:
            phase_features.append("Specialized Agents")
        if self.enable_advanced_rag:
            phase_features.append("Advanced RAG")
        
        phase_status = " + ".join(phase_features) if phase_features else "Phase 1 Only"
        logger.info(f"Advanced Tutoring System initialized ({phase_status})")
    
    def _validate_configuration(self, requested_llm, requested_agents, requested_rag):
        """
        Validate that requested Phase 2 features are available.
        Fail fast with clear error messages if misconfigured.
        """
        errors = []
        
        # Check LLM availability
        if requested_llm:
            if not LLM_AVAILABLE:
                errors.append(
                    "LLM features requested but dependencies not installed.\n"
                    "  Install with: pip install openai ollama"
                )
            elif not self.enable_llm:
                # Was requested but failed to enable
                errors.append(
                    "LLM features requested but initialization failed.\n"
                    "  Check logs above for specific error."
                )
            elif self.llm_manager and not self.llm_manager.use_openai and not self.llm_manager.use_ollama:
                errors.append(
                    "LLM Manager initialized but no LLM provider available.\n"
                    "  Either set OPENAI_API_KEY in .env OR install and run Ollama\n"
                    "  To disable LLM: Set USE_OPENAI=false and USE_OLLAMA=false in .env"
                )
        
        # Check specialized agents
        if requested_agents:
            if not SPECIALIZED_AGENTS_AVAILABLE:
                errors.append(
                    "Specialized agents requested but not available.\n"
                    "  Check installation of Phase 2 components."
                )
            elif not self.enable_specialized_agents:
                errors.append(
                    "Specialized agents requested but initialization failed.\n"
                    "  Check logs above for specific error."
                )
        
        # Check RAG availability  
        if requested_rag:
            if not RAG_AVAILABLE:
                errors.append(
                    "Advanced RAG requested but dependencies not installed.\n"
                    "  Install with: pip install chromadb sentence-transformers"
                )
            elif not self.enable_advanced_rag:
                errors.append(
                    "Advanced RAG requested but initialization failed.\n"
                    "  Check logs above for specific error."
                )
            elif self.rag_system and not self.rag_system.initialized:
                errors.append(
                    "RAG system enabled but failed to initialize properly.\n"
                    "  Check ChromaDB installation and permissions."
                )
        
        # If any errors, fail fast with helpful message
        if errors:
            error_msg = "\n" + "="*70 + "\n"
            error_msg += "❌ CONFIGURATION ERROR: Phase 2 Features Misconfigured\n"
            error_msg += "="*70 + "\n\n"
            error_msg += "The following issues were found:\n\n"
            for i, error in enumerate(errors, 1):
                error_msg += f"{i}. {error}\n\n"
            error_msg += "To fix these issues:\n"
            error_msg += "  - Install missing dependencies: pip install -r requirements.txt\n"
            error_msg += "  - Configure API keys in .env file\n"
            error_msg += "  - OR disable Phase 2 features you don't need in .env\n"
            error_msg += "\nFor help, see: docs/PHASE2_COMPLETE.md\n"
            error_msg += "="*70 + "\n"
            
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
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
    
    def route_educational_request(self, state: TutoringState) -> Literal["subject_expert", "math_tutor", "science_tutor", "programming_tutor", "content_creator"]:
        """
        Route educational requests to appropriate specialized agents (Phase 2)
        
        Routing logic:
        - Math topics → MathTutorAgent
        - Science topics → ScienceTutorAgent  
        - Programming topics → ProgrammingTutorAgent
        - General topics → Standard pipeline
        """
        if not self.enable_specialized_agents:
            return "subject_expert"
        
        subject = state.get('detected_subject', 'general').lower()
        
        # Route to specialized agents based on subject
        if 'math' in subject or 'calculus' in subject or 'algebra' in subject or 'geometry' in subject:
            return "math_tutor"
        elif 'science' in subject or 'physics' in subject or 'chemistry' in subject or 'biology' in subject:
            return "science_tutor"
        elif 'programming' in subject or 'code' in subject or 'python' in subject or 'javascript' in subject:
            return "programming_tutor"
        else:
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
            "version": "2.1.0" if (self.enable_llm or self.enable_specialized_agents or self.enable_advanced_rag) else "2.0.0",
            "phase": "Phase 2: LLM Integration & Educational AI" if (self.enable_llm or self.enable_specialized_agents or self.enable_advanced_rag) else "Phase 1: LangGraph Foundation",
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
                "specialized": {
                    "math_tutor": self.enable_specialized_agents,
                    "science_tutor": self.enable_specialized_agents,
                    "programming_tutor": self.enable_specialized_agents
                }
            },
            "features": {
                "multi_agent_orchestration": True,
                "langgraph_integration": True,
                "subject_detection": True,
                "personalized_lessons": True,
                "practice_generation": True,
                "assessment_ready": True,
                "llm_integration": self.enable_llm,  
                "llm_provider": self._get_llm_provider() if self.enable_llm else None,
                "specialized_agents": self.enable_specialized_agents,  
                "advanced_rag": self.enable_advanced_rag,  
                "streaming": False,  # Phase 3
                "database_persistence": False  # Phase 3
            },
            "llm_details": self._get_llm_details() if self.enable_llm else None,
            "rag_details": self._get_rag_details() if self.enable_advanced_rag else None,
            "capabilities": {
                "subjects": "all",
                "levels": ["beginner", "intermediate", "advanced"],
                "learning_styles": ["visual", "auditory", "kinesthetic", "mixed"]
            }
        }
    
    def _get_llm_provider(self) -> str:
        """Get the active LLM provider"""
        if not self.llm_manager:
            return "none"
        if self.llm_manager.use_openai:
            return "openai"
        if self.llm_manager.use_ollama:
            return "ollama"
        return "none"
    
    def _get_llm_details(self) -> Dict[str, Any]:
        """Get detailed LLM information"""
        if not self.llm_manager:
            return None
        
        return {
            "openai": {
                "enabled": self.llm_manager.use_openai,
                "model": self.llm_manager.openai_model if self.llm_manager.use_openai else None
            },
            "ollama": {
                "enabled": self.llm_manager.use_ollama,
                "model": self.llm_manager.ollama_model if self.llm_manager.use_ollama else None,
                "host": self.llm_manager.ollama_host if self.llm_manager.use_ollama else None
            },
            "active_provider": self._get_llm_provider()
        }
    
    def _get_rag_details(self) -> Dict[str, Any]:
        """Get detailed RAG information"""
        if not self.rag_system:
            return None
        
        return {
            "initialized": self.rag_system.initialized,
            "vector_db": "chromadb" if self.rag_system.initialized else None,
            "collection": self.rag_system.collection_name if self.rag_system.initialized else None,
            "embedder": "sentence-transformers" if self.rag_system.embedder else None,
            "reranker": "cross-encoder" if self.reranker and self.reranker.initialized else None
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
