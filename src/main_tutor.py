# src/main_tutor.py
import os
import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Import the agents
from agents.ai_tutor import UniversalAITutor, LearningProfile
from agents.tutoring_graph import AdvancedTutoringSystem
from agents.state_schema import StudentProfile

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
ai_tutor = None
advanced_system = None
active_students = {}  # Store learning profiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    Modern replacement for @app.on_event
    """
    # Startup
    global ai_tutor, advanced_system
    logger.info("Starting up AI Tutor system...")
    
    try:
        ai_tutor = UniversalAITutor(use_local_model=True)
        advanced_system = AdvancedTutoringSystem(use_local_model=False)
        logger.info("AI Tutor system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize tutoring systems: {str(e)}")
        # Don't raise - allow app to start in degraded mode
    
    yield  # Server runs here
    
    # Shutdown (cleanup if needed)
    logger.info("✓ Shutting down AI Tutor system...")
    # Add cleanup code here if needed (close connections, save state, etc.)

# FastAPI app with lifespan
app = FastAPI(
    title="AI Tutor",
    description="Advanced multi-agent educational tutoring platform with LangGraph orchestration",
    version="1",
    lifespan=lifespan
)

# Request/Response models
class TeachingRequest(BaseModel):
    topic: str
    student_level: str = "beginner"  # beginner, intermediate, advanced
    learning_style: str = "mixed"  # visual, auditory, kinesthetic, mixed
    student_name: str = "Student"
    include_practice: bool = True

class AdvancedTeachingRequest(BaseModel):
    topic: str
    student_level: str = "beginner"
    learning_style: str = "mixed"
    student_name: str = "Student"
    learning_goals: List[str] = []
    use_multi_agent: bool = True

class QuickQuestionRequest(BaseModel):
    question: str
    subject_hint: Optional[str] = None
    student_level: str = "beginner"

class AssessmentRequest(BaseModel):
    topic: str
    student_response: str
    original_question: str

class TeachingResponse(BaseModel):
    status: str
    topic: str
    teaching_session: Dict[str, Any]
    message: str
    cost: str = "0"

class AdvancedTeachingResponse(BaseModel):
    status: str
    topic: str
    teaching_session: Dict[str, Any]
    message: str
    multi_agent_used: bool
    agents_involved: List[str]
    agent_count: int
    cost: str = "0"

class QuestionResponse(BaseModel):
    status: str
    question: str
    answer: Dict[str, Any]
    follow_up_suggestions: List[str]
    cost: str = "0"

@app.get("/", response_class=HTMLResponse)
async def welcome_page():
    """Welcome page for students"""
    return """
    <html>
        <head>
            <title>Advanced AI Tutor</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                .container { max-width: 900px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; }
                .feature { background: rgba(255,255,255,0.2); margin: 10px; padding: 15px; border-radius: 10px; display: inline-block; width: 220px; }
                .new-badge { background: #FFD700; color: #764ba2; padding: 3px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; }
                a { color: #FFD700; text-decoration: none; font-weight: bold; }
                a:hover { text-decoration: underline; }
                .agents { background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>AI Tutor</h1>
                <h3>Multi-Agent Educational Platform</h3>
                <p> Now with LangGraph orchestration!</p>
                
                <div class="feature">
                    <h4>Multi-Agent</h4>
                    <p>6 specialized AI agents working together for better learning</p>
                </div>
                
                <div class="feature">
                    <h4>Any Subject</h4>
                    <p>Math, Science, Programming, Languages, History, Art & more!</p>
                </div>
                
                <div class="feature">
                    <h4>Personalized</h4>
                    <p>Adapts to your level and learning style automatically</p>
                </div>
                
                <div class="agents">
                    <h3>Active Agents</h3>
                    <p style="font-size: 14px;">
                        Subject Expert • Content Creator • Content Retriever<br>
                        Practice Generator • Assessment Agent • Progress Tracker
                    </p>
                </div>
                
                <h3>Quick Links</h3>
                <p><a href="/docs"> API Documentation</a></p>
                <p><a href="/system-status"> System Status</a></p>
                <p><a href="/demo"> Quick Demo</a></p>
                <p><a href="/student-guide"> Student Guide</a></p>
                
                <h4>Try These Topics:</h4>
                <p>"Python programming basics" • "Algebra fundamentals" • "World War 2 causes"<br>
                "How photosynthesis works" • "Spanish grammar rules" • "Drawing techniques"</p>
                
                <p style="margin-top: 30px; font-size: 12px; opacity: 0.8;">
                    Version 2.0.0 - Phase 1: LangGraph Foundation Complete
                </p>
            </div>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Detailed health check for the teaching system"""
    health_status = {
        "status": "healthy",
        "basic_tutor": ai_tutor is not None,
        "advanced_system": advanced_system is not None,
        "multi_agent_enabled": advanced_system is not None,
        "phase": "Phase 1: LangGraph Foundation"
    }
    
    return health_status

@app.get("/system-status")
async def system_status():
    """Get detailed system status"""
    global advanced_system
    
    if not advanced_system:
        return {
            "error": "Advanced system not initialized",
            "basic_tutor_available": ai_tutor is not None
        }
    
    status = advanced_system.get_system_status()
    return {
        **status,
        "graph_visualization": advanced_system.get_graph_visualization(),
        "active_students": len(active_students)
    }

@app.post("/teach", response_model=TeachingResponse)
async def teach_topic(request: TeachingRequest):
    global ai_tutor 
    if not ai_tutor:
        logger.warning("AI Tutor not fully initialized, creating new instance...")
        ai_tutor = UniversalAITutor(use_local_model=request.student_level != "advanced")
    
    try:
        logger.info(f"[BASIC] Teaching request: {request.topic} for {request.student_level} student")
        
        # Create or update student profile
        student_key = f"{request.student_name}_{request.student_level}"
        if student_key not in active_students:
            active_students[student_key] = LearningProfile(
                name=request.student_name,
                level=request.student_level,
                learning_style=request.learning_style
            )
        
        student_profile = active_students[student_key]
        
        # Conduct teaching session
        teaching_session = ai_tutor.teach_topic(request.topic, student_profile)
        
        return TeachingResponse(
            status="success",
            topic=request.topic,
            teaching_session=teaching_session,
            message=f"Teaching session ready! Complete lesson plan for '{request.topic}' at {request.student_level} level.",
            cost="0"
        )
        
    except Exception as e:
        logger.error(f"Teaching error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Teaching failed: {str(e)}"
        )

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuickQuestionRequest):
    """
    Q&A endpoint - PRESERVED FOR BACKWARD COMPATIBILITY
    """
    global ai_tutor  
    try:
        logger.info(f"Quick question: {request.question}")
        
        if not ai_tutor:
            ai_tutor = UniversalAITutor(use_local_model=False)
        
        # Create temporary student profile
        temp_profile = LearningProfile(level=request.student_level)
        
        # Treat question as a mini teaching topic
        teaching_session = ai_tutor.teach_topic(request.question, temp_profile)
        
        # Format as Q&A response
        answer = {
            "explanation": teaching_session["explanation"]["main_explanation"],
            "key_points": teaching_session["explanation"]["key_points"][:3],
            "examples": teaching_session["explanation"]["examples"][:2],
            "subject": teaching_session["detected_subject"],
            "level": teaching_session["teaching_level"]
        }
        
        # Generate follow-up suggestions
        follow_up_suggestions = [
            f"Want to learn more about {teaching_session['detected_subject']}?",
            f"Try asking about: '{request.question} examples'",
            f"Or explore: '{request.question} applications'",
            "Ask me to explain any part in more detail!"
        ]
        
        return QuestionResponse(
            status="success",
            question=request.question,
            answer=answer,
            follow_up_suggestions=follow_up_suggestions,
            cost="0"
        )
        
    except Exception as e:
        logger.error(f"Q&A error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")

@app.post("/assess")
async def assess_student(request: AssessmentRequest):
    """
    Assess student understanding and provide feedback
    """
    global ai_tutor     
    try:
        if not ai_tutor:
            ai_tutor = UniversalAITutor(use_local_model=False)
        
        assessment = ai_tutor.assess_understanding(request.topic, request.student_response)
        
        return {
            "status": "success",
            "topic": request.topic,
            "assessment": assessment,
            "recommendations": {
                "continue_learning": assessment["understanding_level"] in ["good", "developing"],
                "review_needed": assessment["understanding_level"] == "needs_support",
                "next_topics": [f"Advanced {request.topic}", f"{request.topic} applications"],
                "study_methods": ["Practice more examples", "Try explaining to someone else", "Create visual summaries"]
            },
            "encouragement": "Great job engaging with the learning process! Every question helps you grow.",
            "cost": "0"
        }
        
    except Exception as e:
        logger.error(f"Assessment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")
 
@app.post("/teach/advanced", response_model=AdvancedTeachingResponse)
async def teach_advanced(request: AdvancedTeachingRequest):
    """
    Advanced teaching endpoint using multi-agent system
    
    Uses LangGraph orchestration with specialized agents
    """
    global advanced_system
    
    if not advanced_system:
        logger.error("Advanced system not initialized")
        raise HTTPException(
            status_code=503,
            detail="Advanced multi-agent system not available"
        )
    
    try:
        logger.info(f"[MULTI-AGENT] Teaching request: {request.topic} for {request.student_level} student")
        
        # Create or update student profile
        student_key = f"{request.student_name}_{request.student_level}_advanced"
        if student_key not in active_students:
            profile = StudentProfile(
                name=request.student_name,
                level=request.student_level,
                learning_style=request.learning_style,
                learning_goals=request.learning_goals
            )
            active_students[student_key] = profile
        else:
            profile = active_students[student_key]
        
        # Run multi-agent teaching session
        teaching_session = advanced_system.teach_topic(
            topic=request.topic,
            student_profile=profile
        )
        
        return AdvancedTeachingResponse(
            status="success",
            topic=request.topic,
            teaching_session=teaching_session,
            message=f"Multi-agent teaching session completed! {teaching_session['agent_count']} agents collaborated on '{request.topic}'.",
            multi_agent_used=True,
            agents_involved=teaching_session.get('agents_involved', []),
            agent_count=teaching_session.get('agent_count', 0),
            cost="0 - multi-agent orchestration"
        )
        
    except Exception as e:
        logger.error(f"Advanced teaching error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Multi-agent teaching failed: {str(e)}"
        )

@app.post("/practice/personalized")
async def personalized_practice(request: TeachingRequest):
    """
    Generate personalized practice problems using multi-agent system
    """
    global advanced_system
    
    if not advanced_system:
        raise HTTPException(
            status_code=503,
            detail="Advanced system not available"
        )
    
    try:
        logger.info(f"[PRACTICE] Generating personalized practice for: {request.topic}")
        
        # Create student profile
        profile = StudentProfile(
            name=request.student_name,
            level=request.student_level,
            learning_style=request.learning_style
        )
        
        # Run multi-agent system
        session = advanced_system.teach_topic(request.topic, profile)
        
        # Extract practice-focused response
        return {
            "status": "success",
            "topic": request.topic,
            "practice_problems": session.get('practice_problems', []),
            "practice_count": len(session.get('practice_problems', [])),
            "difficulty_level": session.get('teaching_level'),
            "hints_included": True,
            "agents_used": session.get('agents_involved', []),
            "recommendations": session.get('session_feedback', {}).get('recommendations', []),
            "cost": "0"
        }
        
    except Exception as e:
        logger.error(f"Practice generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Practice generation failed: {str(e)}")

@app.post("/assess/understanding")
async def assess_understanding(request: AssessmentRequest):
    """
    Comprehensive assessment using multi-agent system
    
    """
    global advanced_system, ai_tutor
    
    try:
        logger.info(f"[ASSESSMENT] Evaluating understanding of: {request.topic}")
        
        # Use basic tutor for assessment for 
        # Phase 2 of development will have dedicated assessment agent
        if not ai_tutor:
            ai_tutor = UniversalAITutor(use_local_model=False)
        
        assessment = ai_tutor.assess_understanding(request.topic, request.student_response)
        return {
            "status": "success",
            "topic": request.topic,
            "assessment": assessment,
            "detailed_feedback": {
                "understanding_level": assessment["understanding_level"],
                "confidence": assessment["confidence_score"],
                "strengths": assessment.get("strengths", []),
                "areas_for_improvement": assessment.get("areas_for_improvement", []),
                "personalized_recommendations": assessment.get("next_steps", [])
            },
            "next_actions": {
                "review_needed": assessment["understanding_level"] == "needs_support",
                "ready_for_advanced": assessment["understanding_level"] == "good",
                "suggested_next_topics": [f"Advanced {request.topic}", f"{request.topic} applications"]
            },
            "multi_agent_assessment": False,  # Will be True in Phase 2
            "cost": "0"
        }
        
    except Exception as e:
        logger.error(f"Assessment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")
    
@app.get("/demo")
async def demo_lesson():
    """
    Demo endpoint with multi-agent system
    """
    global advanced_system
    
    try:
        if not advanced_system:
            advanced_system = AdvancedTutoringSystem(use_local_model=False)
        
        # Demo with popular topic
        demo_topic = "How machine learning works"
        demo_profile = StudentProfile(level="beginner", learning_style="visual")
        
        demo_session = advanced_system.teach_topic(demo_topic, demo_profile)
        
        return {
            "demo": True,
            "message": "Multi-agent teaching session completed!",
            "topic": demo_topic,
            "multi_agent": True,
            "agents_involved": demo_session.get('agents_involved', []),
            "agent_count": demo_session.get('agent_count', 0),
            "subject_detected": demo_session['detected_subject'],
            "lesson_objectives": demo_session['lesson_plan']['objectives'][:3],
            "sample_explanation": demo_session['explanation']['main_explanation'][:200] + "...",
            "practice_problems_count": len(demo_session['practice_problems']),
            "educational_sources": len(demo_session['educational_content']),
            "learning_progress": demo_session.get('learning_progress', {}),
            "cost": "0",
            "note": "This demonstrates the multi-agent system teaching any topic!"
        }
        
    except Exception as e:
        return {
            "demo": True,
            "error": str(e),
            "message": "Failed",
            "cost": "0"
        }

@app.get("/subjects")
async def list_supported_subjects():
    """Show all subjects the AI tutor can teach"""
    return {
        "supported_subjects": {
            "STEM": ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science", "Engineering", "Statistics"],
            "Languages": ["English", "Spanish", "French", "German", "Mandarin", "Programming Languages", "Linguistics"],
            "Social Studies": ["History", "Geography", "Psychology", "Sociology", "Economics", "Political Science"],
            "Arts & Humanities": ["Art", "Music", "Literature", "Philosophy", "Creative Writing", "Theater"],
            "Practical Skills": ["Study Skills", "Test Preparation", "Research Methods", "Critical Thinking", "Problem Solving"],
            "Technology": ["Web Development", "Data Science", "Artificial Intelligence", "Cybersecurity", "Digital Literacy"]
        },
        "learning_levels": ["Beginner (K-12)", "Intermediate (High School/College)", "Advanced (Graduate/Professional)"],
        "learning_styles": ["Visual (diagrams, charts)", "Auditory (discussion, verbal)", "Kinesthetic (hands-on)", "Mixed (all approaches)"],
        "special_features": [
            "Multi-agent orchestration with LangGraph",
            "6 specialized educational agents",
            "Personalized explanations for your level",
            "Practice problems and quizzes",
            "Progress tracking and assessment",
            "Multiple explanation approaches",
            "Real-world examples and applications"
        ],
        "phase": "Phase 1: LangGraph Foundation Complete",
        "cost": "0",
        "note": "Can teach literally any topic - just ask!"
    }

@app.get("/student-guide")
async def student_guide():
    """Comprehensive guide for students"""
    return {
        "title": "Student Guide to Multi-Agent AI Tutoring",
        "quick_start": [
            "1. Choose any topic you want to learn",
            "2. Specify your level (beginner/intermediate/advanced)",
            "3. Select learning style (visual/auditory/kinesthetic/mixed)",
            "4. Use /teach/advanced for multi-agent experience (recommended)",
            "5. Use /teach for traditional single-agent mode"
        ],
        "endpoints": {
            "/teach/advanced": "Uses all 6 agents for comprehensive learning",
            "/teach": "Original - Single agent, backward compatible",
            "/practice/personalized": "Focused practice problem generation",
            "/assess/understanding": "Enhanced assessment capabilities",
            "/ask": "Quick questions and answers"
        },
        "agents_explained": {
            "subject_expert": "Analyzes your topic and routes to appropriate specialists",
            "content_creator": "Generates personalized lesson plans and explanations",
            "content_retriever": "Finds the best educational resources online",
            "practice_generator": "Creates adaptive practice problems",
            "assessment_agent": "Evaluates your understanding and progress",
            "progress_tracker": "Tracks your learning journey and provides insights"
        },
        "best_practices": {
            "topic_selection": [
                "Be specific: 'Python loops' vs 'programming'",
                "Start broad, then narrow: 'biology' → 'cell structure' → 'mitochondria'",
                "Connect to your goals: 'algebra for engineering'",
                "Ask follow-up questions to go deeper"
            ],
            "learning_effectively": [
                "Start with your actual level, not what you think you should know",
                "Try different learning styles to see what works",
                "Use the practice problems - they really help!",
                "Ask for more examples if something isn't clear",
                "Review previous topics before moving to advanced ones"
            ],
            "using_multi_agent": [
                "Use /teach/advanced for best results",
                "Review the agents_involved field to see which agents helped",
                "Check learning_progress for comprehensive feedback",
                "Follow session_feedback recommendations"
            ]
        },
        "cost": "0",
        "academic_integrity": "Perfect for learning concepts and understanding. Always do your own work for assignments!"
    }

if __name__ == "__main__":
    print("Starting")
    print("Visit: http://localhost:8000 for the web interface")
    print("API docs: http://localhost:8000/docs")
    print()
    
    uvicorn.run(
        "main_tutor:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
