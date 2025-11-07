"""
Real-time educational streaming with WebSocket support
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any, Optional, List
import asyncio
import json
import logging
from datetime import datetime
import uuid
import time

from agents.state_schema import StudentProfile
from agents.tutoring_graph import AdvancedTutoringSystem

logger = logging.getLogger(__name__)


class StreamingSession:
    """Manages a single streaming educational session"""
    
    def __init__(self, session_id: str, websocket: WebSocket, student_profile: StudentProfile):
        self.session_id = session_id
        self.websocket = websocket
        self.student_profile = student_profile
        self.active = True
        self.current_agent = None
        self.message_queue = asyncio.Queue()
        self.start_time = datetime.now()
        
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the client"""
        try:
            await self.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.active = False
    
    async def send_progress(self, agent_name: str, progress: float, details: Dict[str, Any]):
        """Send progress update to client"""
        await self.send_message({
            "type": "progress",
            "agent": agent_name,
            "progress": progress,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def send_content(self, content_type: str, content: Any):
        """Send educational content chunk"""
        await self.send_message({
            "type": "content",
            "content_type": content_type,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    async def send_error(self, error: str):
        """Send error message"""
        await self.send_message({
            "type": "error",
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    async def send_complete(self, summary: Dict[str, Any]):
        """Send session completion message"""
        await self.send_message({
            "type": "complete",
            "summary": summary,
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "timestamp": datetime.now().isoformat()
        })


class EducationalStreamingManager:
    """Manages all streaming educational sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, StreamingSession] = {}
        self.tutoring_system = None
        self.active_connections = 0
        
    async def initialize(self, tutoring_system: Optional[AdvancedTutoringSystem] = None):
        """Initialize with tutoring system"""
        if tutoring_system:
            self.tutoring_system = tutoring_system
        else:
            self.tutoring_system = AdvancedTutoringSystem()
        logger.info("Streaming manager initialized")
    
    async def connect(self, websocket: WebSocket) -> str:
        """Accept WebSocket connection and create session"""
        await websocket.accept()
        session_id = str(uuid.uuid4())
        self.active_connections += 1
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"WebSocket connected: {session_id} (Active: {self.active_connections})")
        return session_id
    
    async def create_session(self, session_id: str, websocket: WebSocket, 
                           student_profile: StudentProfile) -> StreamingSession:
        """Create a new streaming session"""
        session = StreamingSession(session_id, websocket, student_profile)
        self.sessions[session_id] = session
        
        await session.send_message({
            "type": "session_created",
            "session_id": session_id,
            "student_profile": {
                "name": student_profile.name,
                "level": student_profile.level,
                "learning_style": student_profile.learning_style
            },
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Created streaming session: {session_id}")
        return session
    
    async def stream_teaching_session(self, session_id: str, topic: str):
        """Stream a complete teaching session with real-time updates"""
        session = self.sessions.get(session_id)
        if not session or not session.active:
            return
        
        try:
            # Initialize progress tracking
            agents_progress = {
                "subject_expert": {"status": "pending", "progress": 0},
                "content_creator": {"status": "pending", "progress": 0},
                "content_retriever": {"status": "pending", "progress": 0},
                "practice_generator": {"status": "pending", "progress": 0},
                "assessment_agent": {"status": "pending", "progress": 0},
                "progress_tracker": {"status": "pending", "progress": 0}
            }
            
            # Send initial status
            await session.send_content("session_status", {
                "topic": topic,
                "agents": agents_progress
            })
            
            # Simulate progressive content generation
            # Agent 1: Subject Expert Analysis
            await session.send_progress("subject_expert", 0.1, {
                "message": "Analyzing topic complexity...",
                "status": "active"
            })
            await asyncio.sleep(0.5)
            
            await session.send_content("analysis", {
                "topic": topic,
                "detected_subject": "auto-detected",
                "complexity": "moderate",
                "prerequisites": ["basic concepts"],
                "estimated_duration": "20-30 minutes"
            })
            await session.send_progress("subject_expert", 0.2, {
                "message": "Topic analysis complete",
                "status": "complete"
            })
            
            # Agent 2: Content Creation
            await session.send_progress("content_creator", 0.3, {
                "message": "Generating lesson plan...",
                "status": "active"
            })
            await asyncio.sleep(0.5)
            
            # Stream lesson content in chunks
            lesson_sections = [
                {"type": "introduction", "title": f"Introduction to {topic}", 
                 "content": "Let's begin our journey..."},
                {"type": "objectives", "title": "Learning Objectives",
                 "content": ["Understand core concepts", "Apply knowledge", "Practice skills"]},
                {"type": "main_content", "title": "Main Lesson",
                 "content": f"Detailed explanation of {topic}..."}
            ]
            
            for i, section in enumerate(lesson_sections):
                await session.send_content("lesson_section", section)
                progress = 0.3 + (0.2 * ((i + 1) / len(lesson_sections)))
                await session.send_progress("content_creator", progress, {
                    "message": f"Created section: {section['title']}",
                    "status": "active"
                })
                await asyncio.sleep(0.3)
            
            await session.send_progress("content_creator", 0.5, {
                "message": "Lesson plan complete",
                "status": "complete"
            })
            
            # Agent 3: Content Retrieval
            await session.send_progress("content_retriever", 0.55, {
                "message": "Searching for resources...",
                "status": "active"
            })
            await asyncio.sleep(0.5)
            
            await session.send_content("resources", {
                "videos": [{"title": f"{topic} Tutorial", "url": "example.com/video1"}],
                "articles": [{"title": f"Understanding {topic}", "url": "example.com/article1"}],
                "interactive": [{"title": "Practice Tool", "url": "example.com/tool1"}]
            })
            await session.send_progress("content_retriever", 0.65, {
                "message": "Resources found",
                "status": "complete"
            })
            
            # Agent 4: Practice Generation
            await session.send_progress("practice_generator", 0.7, {
                "message": "Creating practice problems...",
                "status": "active"
            })
            await asyncio.sleep(0.5)
            
            # Stream practice problems one by one
            practice_problems = [
                {"id": "p1", "difficulty": "easy", "question": f"Basic {topic} question",
                 "hint": "Think about the fundamentals"},
                {"id": "p2", "difficulty": "medium", "question": f"Apply {topic} concepts",
                 "hint": "Consider the relationships"},
                {"id": "p3", "difficulty": "hard", "question": f"Advanced {topic} challenge",
                 "hint": "Combine multiple concepts"}
            ]
            
            for problem in practice_problems:
                await session.send_content("practice_problem", problem)
                await asyncio.sleep(0.3)
            
            await session.send_progress("practice_generator", 0.85, {
                "message": "Practice problems ready",
                "status": "complete"
            })
            
            # Agent 5: Assessment Creation
            await session.send_progress("assessment_agent", 0.9, {
                "message": "Preparing assessment...",
                "status": "active"
            })
            await asyncio.sleep(0.5)
            
            await session.send_content("assessment", {
                "type": "quiz",
                "questions": [
                    {"id": "q1", "question": f"What is {topic}?", "type": "multiple_choice"},
                    {"id": "q2", "question": f"How do you apply {topic}?", "type": "short_answer"}
                ],
                "passing_score": 0.7
            })
            await session.send_progress("assessment_agent", 0.95, {
                "message": "Assessment prepared",
                "status": "complete"
            })
            
            # Agent 6: Progress Tracking
            await session.send_progress("progress_tracker", 0.98, {
                "message": "Finalizing session...",
                "status": "active"
            })
            await asyncio.sleep(0.3)
            
            # Send completion summary
            await session.send_complete({
                "topic": topic,
                "agents_used": list(agents_progress.keys()),
                "content_created": {
                    "lesson_sections": len(lesson_sections),
                    "practice_problems": len(practice_problems),
                    "resources": 3,
                    "assessment_questions": 2
                },
                "estimated_completion_time": "25 minutes",
                "next_steps": ["Review materials", "Complete practice", "Take assessment"]
            })
            
            await session.send_progress("progress_tracker", 1.0, {
                "message": "Session complete!",
                "status": "complete"
            })
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            await session.send_error(str(e))
    
    async def handle_student_interaction(self, session_id: str, interaction: Dict[str, Any]):
        """Handle real-time student interactions"""
        session = self.sessions.get(session_id)
        if not session or not session.active:
            return
        
        interaction_type = interaction.get("type")
        
        try:
            if interaction_type == "ask_question":
                question = interaction.get("question")
                
                # Send thinking indicator
                await session.send_content("thinking", {
                    "message": "Processing your question..."
                })
                
                # Simulate processing
                await asyncio.sleep(1)
                
                # Send answer
                await session.send_content("answer", {
                    "question": question,
                    "answer": f"Here's the answer to your question about {question}...",
                    "confidence": 0.85,
                    "sources": ["lesson_content", "knowledge_base"]
                })
                
            elif interaction_type == "request_hint":
                problem_id = interaction.get("problem_id")
                await session.send_content("hint", {
                    "problem_id": problem_id,
                    "hint": "Consider breaking down the problem into smaller parts...",
                    "level": 1
                })
                
            elif interaction_type == "submit_answer":
                problem_id = interaction.get("problem_id")
                answer = interaction.get("answer")
                
                # Simulate evaluation
                await session.send_content("evaluating", {
                    "message": "Evaluating your answer..."
                })
                await asyncio.sleep(0.5)
                
                # Send feedback
                await session.send_content("feedback", {
                    "problem_id": problem_id,
                    "correct": True,  # Simplified for demo
                    "feedback": "Well done! Your understanding is correct.",
                    "explanation": "Here's why this works...",
                    "score": 1.0
                })
                
            elif interaction_type == "adjust_difficulty":
                new_level = interaction.get("level")
                session.student_profile.level = new_level
                await session.send_content("settings_updated", {
                    "level": new_level,
                    "message": f"Difficulty adjusted to {new_level}"
                })
                
            elif interaction_type == "request_explanation":
                concept = interaction.get("concept")
                await session.send_content("explanation", {
                    "concept": concept,
                    "explanation": f"Let me explain {concept} in detail...",
                    "examples": ["Example 1", "Example 2"],
                    "visual_aid": None  # Could include diagram URLs
                })
                
        except Exception as e:
            logger.error(f"Interaction handling error: {e}")
            await session.send_error(f"Failed to process interaction: {str(e)}")
    
    async def disconnect(self, session_id: str):
        """Handle disconnection"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.active = False
            del self.sessions[session_id]
            self.active_connections -= 1
            logger.info(f"WebSocket disconnected: {session_id} (Active: {self.active_connections})")
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get information about active sessions"""
        return [
            {
                "session_id": sid,
                "student_name": session.student_profile.name,
                "start_time": session.start_time.isoformat(),
                "active": session.active
            }
            for sid, session in self.sessions.items()
        ]


# Global streaming manager instance
streaming_manager = EducationalStreamingManager()
