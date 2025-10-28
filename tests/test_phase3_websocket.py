"""
Unit tests for Phase 3 WebSocket streaming functionality
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime

from fastapi import WebSocket
from api.educational_streaming import (
    StreamingSession, EducationalStreamingManager, streaming_manager
)
from api.websocket_routes import websocket_endpoint
from agents.state_schema import StudentProfile


class TestStreamingSession:
    """Test StreamingSession class"""
    
    @pytest.mark.asyncio
    async def test_create_session(self):
        """Test creating a streaming session"""
        # Mock WebSocket
        mock_ws = Mock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        
        # Create student profile
        student_profile = StudentProfile(
            name="Test Student",
            level="beginner",
            learning_style="visual"
        )
        
        # Create session
        session = StreamingSession("test-session-id", mock_ws, student_profile)
        
        assert session.session_id == "test-session-id"
        assert session.student_profile.name == "Test Student"
        assert session.active is True
    
    @pytest.mark.asyncio
    async def test_send_progress(self):
        """Test sending progress updates"""
        mock_ws = Mock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        
        student_profile = StudentProfile(name="Test", level="beginner")
        session = StreamingSession("test-id", mock_ws, student_profile)
        
        # Send progress
        await session.send_progress("subject_expert", 0.5, {"message": "Analyzing..."})
        
        # Verify message sent
        mock_ws.send_json.assert_called_once()
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "progress"
        assert call_args["agent"] == "subject_expert"
        assert call_args["progress"] == 0.5
    
    @pytest.mark.asyncio
    async def test_send_content(self):
        """Test sending content chunks"""
        mock_ws = Mock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        
        student_profile = StudentProfile(name="Test", level="beginner")
        session = StreamingSession("test-id", mock_ws, student_profile)
        
        # Send content
        content = {"title": "Lesson 1", "objectives": ["Learn", "Practice"]}
        await session.send_content("lesson", content)
        
        # Verify message sent
        mock_ws.send_json.assert_called_once()
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "content"
        assert call_args["content_type"] == "lesson"
        assert call_args["content"] == content
    
    @pytest.mark.asyncio
    async def test_send_error(self):
        """Test sending error messages"""
        mock_ws = Mock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        
        student_profile = StudentProfile(name="Test", level="beginner")
        session = StreamingSession("test-id", mock_ws, student_profile)
        
        # Send error
        await session.send_error("Test error message")
        
        # Verify message sent
        mock_ws.send_json.assert_called_once()
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["error"] == "Test error message"
    
    @pytest.mark.asyncio
    async def test_send_complete(self):
        """Test sending completion message"""
        mock_ws = Mock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        
        student_profile = StudentProfile(name="Test", level="beginner")
        session = StreamingSession("test-id", mock_ws, student_profile)
        
        # Send completion
        summary = {"topic": "Python", "agents_used": ["subject_expert"]}
        await session.send_complete(summary)
        
        # Verify message sent
        mock_ws.send_json.assert_called_once()
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "complete"
        assert call_args["summary"] == summary
        assert "duration" in call_args


class TestEducationalStreamingManager:
    """Test EducationalStreamingManager class"""
    
    @pytest.mark.asyncio
    async def test_initialize_manager(self):
        """Test manager initialization"""
        manager = EducationalStreamingManager()
        await manager.initialize()
        
        assert manager.tutoring_system is not None
        assert manager.active_connections == 0
        assert len(manager.sessions) == 0
    
    @pytest.mark.asyncio
    async def test_connect_websocket(self):
        """Test WebSocket connection"""
        manager = EducationalStreamingManager()
        await manager.initialize()
        
        # Mock WebSocket
        mock_ws = Mock(spec=WebSocket)
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        
        # Connect
        session_id = await manager.connect(mock_ws)
        
        assert session_id is not None
        assert manager.active_connections == 1
        mock_ws.accept.assert_called_once()
        mock_ws.send_json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_session(self):
        """Test creating a streaming session"""
        manager = EducationalStreamingManager()
        await manager.initialize()
        
        # Mock WebSocket
        mock_ws = Mock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        
        # Create student profile
        student_profile = StudentProfile(
            name="Test Student",
            level="intermediate",
            learning_style="kinesthetic"
        )
        
        # Create session
        session_id = "test-session-123"
        session = await manager.create_session(session_id, mock_ws, student_profile)
        
        assert session_id in manager.sessions
        assert session.student_profile.name == "Test Student"
        assert session.student_profile.level == "intermediate"
    
    @pytest.mark.asyncio
    async def test_disconnect_session(self):
        """Test disconnecting a session"""
        manager = EducationalStreamingManager()
        await manager.initialize()
        
        # Create mock session
        mock_ws = Mock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        
        session_id = "test-session-456"
        student_profile = StudentProfile(name="Test", level="beginner")
        await manager.create_session(session_id, mock_ws, student_profile)
        
        # Disconnect
        await manager.disconnect(session_id)
        
        assert session_id not in manager.sessions
    
    @pytest.mark.asyncio
    async def test_stream_teaching_session(self):
        """Test streaming a teaching session"""
        manager = EducationalStreamingManager()
        await manager.initialize()
        
        # Create mock session
        mock_ws = Mock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        
        session_id = "test-session-789"
        student_profile = StudentProfile(name="Test", level="beginner")
        await manager.create_session(session_id, mock_ws, student_profile)
        
        # Stream teaching session
        await manager.stream_teaching_session(session_id, "Python Basics")
        
        # Verify multiple messages were sent
        assert mock_ws.send_json.call_count > 5  # Progress, content, completion
    
    @pytest.mark.asyncio
    async def test_handle_student_interaction_question(self):
        """Test handling student questions"""
        manager = EducationalStreamingManager()
        await manager.initialize()
        
        # Create mock session
        mock_ws = Mock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        
        session_id = "test-session-question"
        student_profile = StudentProfile(name="Test", level="beginner")
        await manager.create_session(session_id, mock_ws, student_profile)
        
        # Handle question interaction
        interaction = {
            "type": "ask_question",
            "question": "What is a variable?"
        }
        await manager.handle_student_interaction(session_id, interaction)
        
        # Verify responses sent
        assert mock_ws.send_json.call_count >= 2  # Thinking + Answer
    
    @pytest.mark.asyncio
    async def test_handle_hint_request(self):
        """Test handling hint requests"""
        manager = EducationalStreamingManager()
        await manager.initialize()
        
        # Create mock session
        mock_ws = Mock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        
        session_id = "test-session-hint"
        student_profile = StudentProfile(name="Test", level="beginner")
        await manager.create_session(session_id, mock_ws, student_profile)
        
        # Handle hint request
        interaction = {
            "type": "request_hint",
            "problem_id": "p1"
        }
        await manager.handle_student_interaction(session_id, interaction)
        
        # Verify hint sent
        mock_ws.send_json.assert_called()
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "content"
        assert call_args["content_type"] == "hint"
    
    @pytest.mark.asyncio
    async def test_handle_answer_submission(self):
        """Test handling answer submissions"""
        manager = EducationalStreamingManager()
        await manager.initialize()
        
        # Create mock session
        mock_ws = Mock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        
        session_id = "test-session-answer"
        student_profile = StudentProfile(name="Test", level="beginner")
        await manager.create_session(session_id, mock_ws, student_profile)
        
        # Handle answer submission
        interaction = {
            "type": "submit_answer",
            "problem_id": "p1",
            "answer": "42"
        }
        await manager.handle_student_interaction(session_id, interaction)
        
        # Verify feedback sent
        assert mock_ws.send_json.call_count >= 2  # Evaluating + Feedback
    
    @pytest.mark.asyncio
    async def test_get_active_sessions(self):
        """Test getting active sessions info"""
        manager = EducationalStreamingManager()
        await manager.initialize()
        
        # Create multiple sessions
        for i in range(3):
            mock_ws = Mock(spec=WebSocket)
            mock_ws.send_json = AsyncMock()
            session_id = f"session-{i}"
            student_profile = StudentProfile(name=f"Student {i}", level="beginner")
            await manager.create_session(session_id, mock_ws, student_profile)
        
        # Get active sessions
        active = manager.get_active_sessions()
        
        assert len(active) == 3
        assert all("session_id" in s for s in active)
        assert all("student_name" in s for s in active)


class TestWebSocketEndpoint:
    """Test WebSocket endpoint functionality"""
    
    @pytest.mark.asyncio
    async def test_websocket_initialization(self):
        """Test WebSocket connection initialization"""
        # Mock WebSocket
        mock_ws = Mock(spec=WebSocket)
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.receive_text = AsyncMock()
        
        # Mock receive_text to return initialization message then disconnect
        mock_ws.receive_text.side_effect = [
            json.dumps({
                "type": "initialize",
                "student": {
                    "name": "Test Student",
                    "level": "beginner",
                    "learning_style": "visual"
                }
            }),
            json.dumps({"type": "disconnect"})
        ]
        
        # Test endpoint
        with patch('api.websocket_routes.streaming_manager') as mock_manager:
            mock_manager.connect = AsyncMock(return_value="test-session")
            mock_manager.create_session = AsyncMock()
            mock_manager.disconnect = AsyncMock()
            
            await websocket_endpoint(mock_ws)
            
            # Verify connection established
            mock_manager.connect.assert_called_once()
            mock_manager.create_session.assert_called_once()
            mock_manager.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_teach_message(self):
        """Test handling teach message"""
        # Mock WebSocket
        mock_ws = Mock(spec=WebSocket)
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.receive_text = AsyncMock()
        
        # Mock messages
        mock_ws.receive_text.side_effect = [
            json.dumps({
                "type": "initialize",
                "student": {"name": "Test", "level": "beginner"}
            }),
            json.dumps({
                "type": "teach",
                "topic": "Python Basics",
                "level": "beginner"
            }),
            json.dumps({"type": "disconnect"})
        ]
        
        # Test endpoint
        with patch('api.websocket_routes.streaming_manager') as mock_manager:
            mock_manager.connect = AsyncMock(return_value="test-session")
            mock_manager.create_session = AsyncMock()
            mock_manager.stream_teaching_session = AsyncMock()
            mock_manager.disconnect = AsyncMock()
            mock_manager.sessions = {"test-session": Mock()}
            
            await websocket_endpoint(mock_ws)
            
            # Verify teaching session started
            mock_manager.stream_teaching_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_interaction_message(self):
        """Test handling interaction messages"""
        # Mock WebSocket
        mock_ws = Mock(spec=WebSocket)
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.receive_text = AsyncMock()
        
        # Mock messages
        mock_ws.receive_text.side_effect = [
            json.dumps({
                "type": "initialize",
                "student": {"name": "Test", "level": "beginner"}
            }),
            json.dumps({
                "type": "interaction",
                "interaction": {
                    "type": "ask_question",
                    "question": "What is Python?"
                }
            }),
            json.dumps({"type": "disconnect"})
        ]
        
        # Test endpoint
        with patch('api.websocket_routes.streaming_manager') as mock_manager:
            mock_manager.connect = AsyncMock(return_value="test-session")
            mock_manager.create_session = AsyncMock()
            mock_manager.handle_student_interaction = AsyncMock()
            mock_manager.disconnect = AsyncMock()
            
            await websocket_endpoint(mock_ws)
            
            # Verify interaction handled
            mock_manager.handle_student_interaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_heartbeat(self):
        """Test heartbeat/ping-pong mechanism"""
        # Mock WebSocket
        mock_ws = Mock(spec=WebSocket)
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.receive_text = AsyncMock()
        
        # Mock messages
        mock_ws.receive_text.side_effect = [
            json.dumps({
                "type": "initialize",
                "student": {"name": "Test", "level": "beginner"}
            }),
            json.dumps({"type": "ping"}),
            json.dumps({"type": "disconnect"})
        ]
        
        # Test endpoint
        with patch('api.websocket_routes.streaming_manager') as mock_manager:
            mock_manager.connect = AsyncMock(return_value="test-session")
            mock_manager.create_session = AsyncMock()
            mock_manager.disconnect = AsyncMock()
            
            await websocket_endpoint(mock_ws)
            
            # Verify pong response sent
            pong_sent = False
            for call in mock_ws.send_json.call_args_list:
                if call[0][0].get("type") == "pong":
                    pong_sent = True
                    break
            assert pong_sent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
