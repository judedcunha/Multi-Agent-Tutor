# src/main_tutor.py
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Import the agents
from agents.ai_tutor import UniversalAITutor, LearningProfile
from agents.tutoring_graph import AdvancedTutoringSystem
from agents.state_schema import StudentProfile

# Phase 3 imports
from api.educational_streaming import streaming_manager
from api.websocket_routes import websocket_endpoint, websocket_admin
from database.db_manager import db_manager, get_db
from database.educational_crud import educational_crud, analytics_crud
from optimization.educational_caching import cache_manager
from monitoring.educational_analytics import analytics_manager

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
        # Initialize Phase 1-2 systems
        ai_tutor = UniversalAITutor(use_local_model=True)
        advanced_system = AdvancedTutoringSystem(use_local_model=False)
        logger.info("AI Tutor system initialized successfully")
        
        # Phase 3: Initialize database
        db_manager.initialize()
        logger.info("Database initialized")
        
        # Phase 3: Initialize Redis cache
        cache_manager.initialize()
        logger.info("Redis cache initialized")
        
        # Phase 3: Initialize streaming manager
        await streaming_manager.initialize(advanced_system)
        logger.info("WebSocket streaming initialized")
        
        # Phase 3: Initialize analytics manager
        analytics_manager.initialize()
        logger.info("Analytics system initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize systems: {str(e)}")
        # Don't raise - allow app to start in degraded mode
    
    yield  # Server runs here
    
    # Shutdown (cleanup if needed)
    logger.info("Shutting down AI Tutor system...")
    # Clean up database connections
    db_manager.close()
    logger.info("Cleanup complete")

# FastAPI app with lifespan
app = FastAPI(
    title="AI Tutor",
    description="Advanced multi-agent educational tutoring platform with LangGraph orchestration and real-time streaming",
    version="3.0",
    lifespan=lifespan
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Phase 3: WebSocket endpoints
@app.websocket("/ws/learn")
async def websocket_learn(websocket: WebSocket):
    """WebSocket endpoint for real-time learning sessions"""
    await websocket_endpoint(websocket)


@app.websocket("/ws/admin")
async def websocket_admin_endpoint(websocket: WebSocket):
    """Admin WebSocket endpoint for monitoring active sessions"""
    await websocket_admin(websocket)


# Phase 3: Database endpoints
@app.post("/students/create")
async def create_student(
    name: str,
    email: Optional[str] = None,
    level: str = "beginner",
    learning_style: str = "mixed",
    db: Session = Depends(get_db)
):
    """Create a new student profile"""
    student = educational_crud.create_student(db, name, email, level, learning_style)
    return {
        "status": "success",
        "student_id": student.student_id,
        "message": f"Student profile created for {name}"
    }


@app.get("/students/{student_id}")
async def get_student(student_id: str, db: Session = Depends(get_db)):
    """Get student profile and progress"""
    student = educational_crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    progress = educational_crud.get_student_progress_summary(db, student_id)
    
    return {
        "student": {
            "id": student.student_id,
            "name": student.name,
            "level": student.level,
            "learning_style": student.learning_style
        },
        "progress": progress
    }


@app.get("/students/{student_id}/history")
async def get_student_history(
    student_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get student's learning history"""
    history = educational_crud.get_student_history(db, student_id, limit)
    return {
        "student_id": student_id,
        "sessions": [
            {
                "session_id": s.session_id,
                "topic": s.topic,
                "subject": s.subject,
                "started_at": s.started_at.isoformat(),
                "duration_minutes": s.duration_minutes
            }
            for s in history
        ]
    }


@app.delete("/students/{student_id}")
async def delete_student(student_id: str, db: Session = Depends(get_db)):
    """Delete a student and all related data (GDPR compliance)"""
    success = educational_crud.delete_student(db, student_id)
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    return {
        "status": "success",
        "message": f"Student {student_id} and all related data deleted"
    }


@app.get("/streaming/status")
async def get_streaming_status():
    """Get WebSocket streaming status"""
    active_sessions = streaming_manager.get_active_sessions()
    return {
        "active_connections": streaming_manager.active_connections,
        "sessions": active_sessions,
        "status": "operational"
    }


# Phase 3: Analytics Endpoints

class AnalyticsRequest(BaseModel):
    """Request model for analytics operations"""
    student_id: str
    session_id: Optional[str] = None
    topic: Optional[str] = None
    time_range: str = "week"  # day, week, month

class PracticeAttemptRequest(BaseModel):
    """Request model for recording practice attempts"""
    session_id: str
    student_id: str
    problem_number: int
    problem_text: str
    topic: str
    difficulty: str = "medium"
    student_answer: str
    correct: bool
    time_spent: int  # seconds
    hints_used: int = 0

class InteractionRequest(BaseModel):
    """Request model for recording interactions"""
    session_id: str
    interaction_type: str  # question, hint_request, submission
    agent_name: str
    response_time_ms: int


@app.get("/analytics/student/{student_id}")
def get_student_analytics(
    student_id: str,
    time_range: str = "week",
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics for a student"""
    try:
        # Get analytics from manager
        analytics = analytics_manager.get_student_analytics(
            student_id=student_id,
            time_range=time_range
        )
        
        # Get additional data from CRUD if needed
        summary = analytics_crud.get_student_analytics_summary(db, student_id)
        
        return {
            "status": "success",
            "student_id": student_id,
            "time_range": time_range,
            "analytics": analytics,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error fetching student analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )


@app.get("/analytics/topic/{student_id}/{topic}")
def get_topic_performance(
    student_id: str,
    topic: str,
    db: Session = Depends(get_db)
):
    """Get detailed performance analytics for a specific topic"""
    try:
        # Get from analytics manager
        performance = analytics_manager.get_topic_performance(
            student_id=student_id,
            topic=topic
        )
        
        # Get trends from CRUD
        trends = analytics_crud.get_topic_trends(db, student_id, topic)
        
        return {
            "status": "success",
            "student_id": student_id,
            "topic": topic,
            "performance": performance,
            "trends": trends
        }
        
    except Exception as e:
        logger.error(f"Error fetching topic performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve topic performance: {str(e)}"
        )


@app.get("/analytics/dashboard/{student_id}")
def get_dashboard_data(
    student_id: str,
    time_range: str = "week",
    db: Session = Depends(get_db)
):
    """Get all dashboard data for a student"""
    try:
        # Main analytics
        analytics = analytics_manager.get_student_analytics(
            student_id=student_id,
            time_range=time_range
        )
        
        # Learning streaks
        streaks = analytics_manager.get_learning_streaks(student_id)
        
        # Learning streak from CRUD
        streak_data = analytics_crud.calculate_learning_streak(db, student_id)
        
        # Get student info
        student = educational_crud.get_student(db, student_id)
        
        return {
            "status": "success",
            "student": {
                "id": student.student_id if student else student_id,
                "name": student.name if student else "Unknown",
                "level": student.level if student else "beginner",
                "learning_style": student.learning_style if student else "mixed"
            },
            "analytics": analytics,
            "streaks": {
                **streaks,
                **streak_data
            },
            "time_range": time_range,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve dashboard data: {str(e)}"
        )


@app.post("/analytics/session/start")
def start_analytics_session(
    session_id: str,
    student_id: str,
    topic: str,
    subject: str,
    level: str = "beginner"
):
    """Start tracking a learning session"""
    try:
        result = analytics_manager.record_session_start(
            session_id=session_id,
            student_id=student_id,
            topic=topic,
            subject=subject,
            level=level
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error starting analytics session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start analytics session: {str(e)}"
        )


@app.post("/analytics/session/end")
def end_analytics_session(
    session_id: str,
    engagement_score: Optional[float] = None,
    completion_rate: Optional[float] = None
):
    """End a learning session and compute final metrics"""
    try:
        result = analytics_manager.record_session_end(
            session_id=session_id,
            engagement_score=engagement_score,
            completion_rate=completion_rate
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error ending analytics session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to end analytics session: {str(e)}"
        )


@app.post("/analytics/practice/attempt")
def record_practice_attempt(request: PracticeAttemptRequest):
    """Record a practice problem attempt"""
    try:
        result = analytics_manager.record_practice_attempt(
            session_id=request.session_id,
            student_id=request.student_id,
            problem_number=request.problem_number,
            problem_text=request.problem_text,
            topic=request.topic,
            difficulty=request.difficulty,
            student_answer=request.student_answer,
            correct=request.correct,
            time_spent=request.time_spent,
            hints_used=request.hints_used
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error recording practice attempt: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record practice attempt: {str(e)}"
        )


@app.post("/analytics/interaction")
def record_interaction(request: InteractionRequest):
    """Record an interaction during a learning session"""
    try:
        analytics_manager.record_interaction(
            session_id=request.session_id,
            interaction_type=request.interaction_type,
            agent_name=request.agent_name,
            response_time_ms=request.response_time_ms
        )
        
        return {
            "status": "success",
            "message": "Interaction recorded"
        }
        
    except Exception as e:
        logger.error(f"Error recording interaction: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record interaction: {str(e)}"
        )


@app.post("/analytics/metrics/compute")
def compute_daily_metrics(
    student_id: str,
    date: Optional[str] = None  # ISO format date
):
    """Compute and store daily metrics for a student"""
    try:
        target_date = datetime.fromisoformat(date) if date else datetime.utcnow()
        
        analytics_manager.compute_daily_metrics(
            student_id=student_id,
            date=target_date
        )
        
        return {
            "status": "success",
            "message": f"Daily metrics computed for {student_id}",
            "date": target_date.date().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error computing daily metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute daily metrics: {str(e)}"
        )


@app.get("/analytics/streaks/{student_id}")
def get_learning_streaks(
    student_id: str,
    db: Session = Depends(get_db)
):
    """Get learning streak information for a student"""
    try:
        # Get from analytics manager
        streaks = analytics_manager.get_learning_streaks(student_id)
        
        # Also get from CRUD for comparison
        crud_streaks = analytics_crud.calculate_learning_streak(db, student_id)
        
        return {
            "status": "success",
            "student_id": student_id,
            "current_streak": max(streaks.get('current_streak', 0), 
                                 crud_streaks.get('current_streak', 0)),
            "longest_streak": max(streaks.get('longest_streak', 0),
                                 crud_streaks.get('longest_streak', 0)),
            "total_active_days": streaks.get('total_active_days', 0),
            "last_active": streaks.get('last_active')
        }
        
    except Exception as e:
        logger.error(f"Error fetching learning streaks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve learning streaks: {str(e)}"
        )


# Phase 3: Cache Management Endpoints
@app.get("/cache/stats")
async def get_cache_stats():
    """Get Redis cache statistics"""
    stats = cache_manager.get_cache_stats()
    return {
        "cache": stats,
        "message": "Cache statistics retrieved successfully"
    }


@app.get("/cache/counters")
async def get_cache_counters():
    """Get cache hit/miss counters for all operations"""
    counters = {
        "lesson": {
            "hits": cache_manager.get_counter("lesson_cache_hits"),
            "misses": cache_manager.get_counter("lesson_cache_misses"),
            "hit_rate": 0.0
        },
        "practice": {
            "hits": cache_manager.get_counter("practice_cache_hits"),
            "misses": cache_manager.get_counter("practice_cache_misses"),
            "hit_rate": 0.0
        },
        "rag": {
            "hits": cache_manager.get_counter("rag_cache_hits"),
            "misses": cache_manager.get_counter("rag_cache_misses"),
            "hit_rate": 0.0
        },
        "total": {
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0
        }
    }
    
    # Calculate hit rates
    for key in ["lesson", "practice", "rag"]:
        hits = counters[key]["hits"]
        misses = counters[key]["misses"]
        total = hits + misses
        if total > 0:
            counters[key]["hit_rate"] = round(hits / total, 3)
        counters["total"]["hits"] += hits
        counters["total"]["misses"] += misses
    
    # Calculate total hit rate
    total_hits = counters["total"]["hits"]
    total_misses = counters["total"]["misses"]
    total_requests = total_hits + total_misses
    if total_requests > 0:
        counters["total"]["hit_rate"] = round(total_hits / total_requests, 3)
    
    return {
        "counters": counters,
        "total_requests": total_requests,
        "cache_enabled": cache_manager.enabled
    }


@app.post("/cache/clear")
async def clear_cache(pattern: Optional[str] = None):
    """Clear cache entries with optional pattern matching"""
    cache_manager.clear_cache(pattern)
    
    message = f"Cache cleared for pattern: {pattern}" if pattern else "All cache entries cleared"
    
    return {
        "status": "success",
        "message": message,
        "pattern": pattern
    }


@app.post("/cache/warm")
async def warm_cache(
    topics: List[str] = ["Python basics", "Mathematics", "Science"],
    levels: List[str] = ["beginner", "intermediate"],
    learning_styles: List[str] = ["visual", "mixed"]
):
    """Warm the cache with common queries (pre-populate)"""
    warmed_count = 0
    
    for topic in topics:
        for level in levels:
            for style in learning_styles:
                # Check if already cached
                if not cache_manager.get_lesson(topic, level, style):
                    # Would normally generate and cache here
                    # For now, just count what would be warmed
                    warmed_count += 1
    
    return {
        "status": "success",
        "message": f"Cache warming initiated for {warmed_count} combinations",
        "topics": topics,
        "levels": levels,
        "learning_styles": learning_styles
    }


@app.get("/cache/info")
async def get_cache_info():
    """Get detailed cache configuration and status"""
    return {
        "enabled": cache_manager.enabled,
        "default_ttl": cache_manager.default_ttl,
        "redis_connected": cache_manager.redis_client is not None,
        "ttl_settings": {
            "lessons": "1 hour",
            "practice_problems": "30 minutes",
            "rag_results": "30 minutes",
            "student_sessions": "2 hours"
        },
        "cache_keys_pattern": "tutor:*",
        "features": {
            "lesson_caching": "Enabled",
            "practice_caching": "Enabled",
            "rag_caching": "Enabled",
            "session_caching": "Enabled",
            "sliding_expiration": "Supported"
        }
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
