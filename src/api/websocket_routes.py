"""
WebSocket routes for real-time educational streaming
"""

from fastapi import WebSocket, WebSocketDisconnect, Query
from typing import Optional
import logging
import json

from agents.state_schema import StudentProfile
from api.educational_streaming import streaming_manager
from database.db_manager import get_db, db_manager
from database.educational_crud import educational_crud
from datetime import datetime
import time

logger = logging.getLogger(__name__)


async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for educational streaming"""
    session_id = None
    student_id = None
    
    try:
        # Connect to WebSocket
        session_id = await streaming_manager.connect(websocket)
        
        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get("type")
                
                if message_type == "initialize":
                    # Initialize student session
                    student_data = message.get("student", {})
                    student_profile = StudentProfile(
                        name=student_data.get("name", "Student"),
                        level=student_data.get("level", "beginner"),
                        learning_style=student_data.get("learning_style", "mixed")
                    )
                    
                    # Create or get student from database if email provided
                    if student_data.get("email"):
                        db = next(get_db())
                        try:
                            student = educational_crud.get_student_by_email(
                                db, student_data["email"]
                            )
                            if not student:
                                student = educational_crud.create_student(
                                    db,
                                    name=student_data.get("name"),
                                    email=student_data.get("email"),
                                    level=student_data.get("level", "beginner"),
                                    learning_style=student_data.get("learning_style", "mixed")
                                )
                            student_id = student.student_id
                        finally:
                            db.close()
                    
                    # Create streaming session
                    session = await streaming_manager.create_session(
                        session_id, websocket, student_profile
                    )
                    
                elif message_type == "teach":
                    # Start teaching session
                    topic = message.get("topic")
                    if topic and session_id in streaming_manager.sessions:
                        
                        # Create database session if student exists
                        if student_id:
                            db = next(get_db())
                            try:
                                db_session = educational_crud.create_learning_session(
                                    db,
                                    student_id=student_id,
                                    topic=topic,
                                    subject="auto-detected",
                                    level=message.get("level", "beginner")
                                )
                            finally:
                                db.close()
                        
                        # Stream the teaching session
                        await streaming_manager.stream_teaching_session(session_id, topic)
                        
                elif message_type == "interaction":
                    # Handle student interaction
                    await streaming_manager.handle_student_interaction(
                        session_id, message.get("interaction", {})
                    )
                    
                elif message_type == "ping":
                    # Heartbeat/keepalive
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                elif message_type == "disconnect":
                    # Client-initiated disconnect
                    break
                    
                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Unknown message type: {message_type}"
                    })
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected normally: {session_id}")
                break
            except json.JSONDecodeError as e:
                await websocket.send_json({
                    "type": "error",
                    "error": f"Invalid JSON: {str(e)}"
                })
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "error": str(e)
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected during initialization: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": f"Connection error: {str(e)}"
            })
        except:
            pass
    finally:
        # Clean up session
        if session_id:
            await streaming_manager.disconnect(session_id)


async def websocket_admin(websocket: WebSocket):
    """Admin WebSocket endpoint for monitoring active sessions"""
    await websocket.accept()
    
    try:
        while True:
            # Send active sessions info every 5 seconds
            active_sessions = streaming_manager.get_active_sessions()
            await websocket.send_json({
                "type": "status",
                "active_connections": streaming_manager.active_connections,
                "sessions": active_sessions,
                "timestamp": datetime.now().isoformat()
            })
            
            # Wait for 5 seconds or until a message is received
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                data = json.loads(message)
                
                if data.get("type") == "disconnect":
                    break
                    
            except asyncio.TimeoutError:
                continue
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "error": "Invalid JSON"
                })
                
    except WebSocketDisconnect:
        logger.info("Admin WebSocket disconnected")
    except Exception as e:
        logger.error(f"Admin WebSocket error: {e}")
    finally:
        await websocket.close()


# Import asyncio for admin endpoint
import asyncio
