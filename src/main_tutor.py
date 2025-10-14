# src/main_tutor.py
import os
import logging
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Import the agent
from src.agents.ai_tutor import UniversalAITutor, LearningProfile

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="AI Tutor",
    description="Teach anyone anything using AI",
    version="1.0.0"
)

# Request/Response models
class TeachingRequest(BaseModel):
    topic: str
    student_level: str = "beginner"  # beginner, intermediate, advanced
    learning_style: str = "mixed"  # visual, auditory, kinesthetic, mixed
    student_name: str = "Student"
    include_practice: bool = True

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

class QuestionResponse(BaseModel):
    status: str
    question: str
    answer: Dict[str, Any]
    follow_up_suggestions: List[str]
    cost: str = "0"

# Global instances
ai_tutor = None
active_students = {}  # Store learning profiles

@app.on_event("startup")
async def startup_event():
    global ai_tutor
    
    try:
        ai_tutor = UniversalAITutor(use_local_model=True)
    except Exception as e:
        logger.error(f"Failed to initialize AI Tutor: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def welcome_page():
    """Welcome page for students"""
    return """
    <html>
        <head>
            <title>Universal AI Tutor</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                .container { max-width: 800px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; }
                .feature { background: rgba(255,255,255,0.2); margin: 10px; padding: 15px; border-radius: 10px; display: inline-block; width: 200px; }
                a { color: #FFD700; text-decoration: none; font-weight: bold; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Universal AI Tutor</h1>
                <h3>Teach Anyone Anything</h3>
                
                <div class="feature">
                    <h4>Any Subject</h4>
                    <p>Math, Science, Programming, Languages, History, Art & more!</p>
                </div>
                
                <div class="feature">
                    <h4>Personalized</h4>
                    <p>Adapts to your level and learning style automatically</p>
                </div>
                
                
                <h3>Blah blah</h3>
                <p><a href="/docs">Interactive API Documentation</a></p>
                <p><a href="/demo">Quick Demo</a></p>
                <p><a href="/student-guide">Student Guide</a></p>
                
                <h4>Example Topics to Try:</h4>
                <p>"Python programming basics" • "Algebra fundamentals" • "World War 2 causes"<br>
                "How photosynthesis works" • "Spanish grammar rules" • "Drawing techniques"</p>
            </div>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Detailed health check for the teaching system"""
    health_status = {
        "status": "healthy",
    }
    
    return health_status

@app.post("/teach", response_model=TeachingResponse)
async def teach_topic(request: TeachingRequest):
    """
    Main teaching endpoint 
    """
    if not ai_tutor:
        logger.warning("AI Tutor not fully initialized, creating new instance...")
        ai_tutor = UniversalAITutor(use_local_model=request.student_level != "advanced")
    
    try:
        logger.info(f"Teaching request: {request.topic} for {request.student_level} student")
        
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
    Q&A endpoint
    """
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

@app.get("/demo")
async def demo_lesson():
    """
    Demo endpoint with a sample teaching session
    """
    try:
        if not ai_tutor:
            ai_tutor = UniversalAITutor(use_local_model=False)
        
        # Demo with popular topic
        demo_topic = "How machine learning works"
        demo_profile = LearningProfile(level="beginner", learning_style="visual")
        
        demo_session = ai_tutor.teach_topic(demo_topic, demo_profile)
        
        return {
            "demo": True,
            "message": "Demo teaching session completed!",
            "topic": demo_topic,
            "subject_detected": demo_session['detected_subject'],
            "lesson_objectives": demo_session['lesson_plan']['objectives'][:3],
            "sample_explanation": demo_session['explanation']['main_explanation'][:200] + "...",
            "practice_problems_count": len(demo_session['practice_problems']),
            "educational_sources": len(demo_session['educational_content']),
            "cost": "0",
            "note": "This demonstrates your AI tutor teaching any topic!"
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
    """
    Show all subjects the AI tutor can teach
    """
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
            "Personalized explanations for your level",
            "Practice problems and quizzes",
            "Progress tracking and assessment", 
            "Multiple explanation approaches",
            "Real-world examples and applications"
        ],
        "cost": "0",
        "note": "Can teach literally any topic - just ask!"
    }

@app.get("/student-guide")
async def student_guide():
    """
    Comprehensive guide for students using the AI tutor
    """
    return {
        "title": "Student Guide to AI Tutoring",
        "quick_start": [
            "1. Choose any topic you want to learn",
            "2. Specify your level (beginner/intermediate/advanced)",
            "3. Select learning style (visual/auditory/kinesthetic/mixed)",
            "4. Use /teach endpoint for full lessons",
            "5. Use /ask for quick questions"
        ],
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
            "getting_help": [
                "Ask 'Can you explain this differently?' for alternative explanations",
                "Request 'Give me a simpler example' if confused",
                "Use 'What should I learn next?' for progression guidance",
                "Try 'How does this connect to [other topic]?' for deeper understanding"
            ]
        },
        "example_sessions": {
            "math_student": {
                "request": "Teach me calculus derivatives for beginner level",
                "what_you_get": "Step-by-step lesson plan, visual explanations, practice problems, real-world examples"
            },
            "language_learner": {
                "request": "Spanish grammar rules for intermediate level",
                "what_you_get": "Grammar explanations, usage examples, practice sentences, common mistakes to avoid"
            },
            "programmer": {
                "request": "Machine learning algorithms for advanced level", 
                "what_you_get": "Theory explanations, algorithm comparisons, coding examples, practical applications"
            }
        },
        "study_tips": [
            "Use the AI tutor BEFORE class to preview topics",
            "Take notes on the key points provided",
            "Practice with the generated problems regularly",
            "Review and ask follow-up questions",
            "Share interesting explanations with study groups",
            "Use for homework help and test preparation"
        ],
        "cost": "0",
        "academic_integrity": "Perfect for learning concepts and understanding. Always do your own work for assignments!"
    }

if __name__ == "__main__":
    print("Starting")
    print("Visit: http://localhost:8000 for the web interface")
    print("API docs: http://localhost:8000/docs")
    print()
    
    uvicorn.run(
        "src.main_tutor:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )