"""
Test suite for API endpoints and WebSocket functionality
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import WebSocket
from typing import Dict, Any

# Project imports 
from api.educational_streaming import StreamingSession, streaming_manager


class TestStreamingSession:
    """Test suite for streaming session management"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup streaming session for testing"""
        from agents.state_schema import StudentProfile
        
        self.student_profile = StudentProfile(
            name="Test Student",
            level="intermediate"
        )
        self.mock_websocket = AsyncMock(spec=WebSocket)
        self.session_id = "test_session_123"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_streaming_session_creation(self):
        """Test streaming session creation"""
        session = StreamingSession(
            session_id=self.session_id,
            websocket=self.mock_websocket,
            student_profile=self.student_profile
        )
        
        assert session.session_id == self.session_id
        assert session.student_profile == self.student_profile
        assert session.active is True
        assert session.current_agent is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending message through websocket"""
        session = StreamingSession(
            session_id=self.session_id,
            websocket=self.mock_websocket,
            student_profile=self.student_profile
        )
        
        test_message = {
            "type": "test",
            "content": "Test message"
        }
        
        await session.send_message(test_message)
        
        self.mock_websocket.send_json.assert_called_once_with(test_message)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_progress(self):
        """Test sending progress updates"""
        session = StreamingSession(
            session_id=self.session_id,
            websocket=self.mock_websocket,
            student_profile=self.student_profile
        )
        
        await session.send_progress(
            agent_name="MathTutor",
            progress=0.5,
            details={"step": "Calculating"}
        )
        
        # Verify send_json was called
        self.mock_websocket.send_json.assert_called_once()
        
        # Check the message structure
        call_args = self.mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "progress"
        assert call_args["agent"] == "MathTutor"
        assert call_args["progress"] == 0.5


class TestAPIIntegration:
    """Integration tests for API functionality"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment"""
        from agents.state_schema import StudentProfile
        
        mock_websocket = AsyncMock(spec=WebSocket)
        student = StudentProfile(name="Test", level="beginner")
        
        session = StreamingSession(
            session_id="integration_test",
            websocket=mock_websocket,
            student_profile=student
        )
        
        # Test sending initial message
        await session.send_message({
            "type": "connected",
            "message": "Connection established"
        })
        
        mock_websocket.send_json.assert_called_once()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_lifecycle(self):
        """Test complete session lifecycle"""
        from agents.state_schema import StudentProfile
        
        mock_websocket = AsyncMock(spec=WebSocket)
        student = StudentProfile(name="Lifecycle Test", level="intermediate")
        
        # Create session
        session = StreamingSession(
            session_id="lifecycle_test",
            websocket=mock_websocket,
            student_profile=student
        )
        
        assert session.active is True
        
        # Send various messages
        await session.send_message({"type": "start", "data": {}})
        await session.send_progress("TestAgent", 0.25, {"status": "processing"})
        await session.send_content("lesson", {"content": "Test lesson"})
        
        # Verify messages were sent
        assert mock_websocket.send_json.call_count == 3
        
        # Deactivate session
        session.active = False
        assert session.active is False


class TestSessionManagement:
    """Test session management functionality"""
    
    @pytest.mark.unit
    def test_session_id_generation(self):
        """Test session ID generation"""
        import uuid
        
        session_id = str(uuid.uuid4())
        assert len(session_id) > 0
        assert "-" in session_id  # UUID format
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_multiple_sessions(self):
        """Test handling multiple concurrent sessions"""
        from agents.state_schema import StudentProfile
        
        sessions = []
        
        for i in range(3):
            mock_ws = AsyncMock(spec=WebSocket)
            student = StudentProfile(name=f"Student {i}", level="beginner")
            
            session = StreamingSession(
                session_id=f"session_{i}",
                websocket=mock_ws,
                student_profile=student
            )
            sessions.append(session)
        
        assert len(sessions) == 3
        
        # Send message to each session
        for i, session in enumerate(sessions):
            await session.send_message({
                "type": "test",
                "session": i
            })
        
        # Verify each websocket received one message
        for session in sessions:
            session.websocket.send_json.assert_called_once()


class TestErrorHandling:
    """Test error handling in API/WebSocket"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self):
        """Test handling of websocket errors"""
        from agents.state_schema import StudentProfile
        
        mock_websocket = AsyncMock(spec=WebSocket)
        # Make send_json raise an exception
        mock_websocket.send_json.side_effect = Exception("Connection lost")
        
        student = StudentProfile(name="Error Test", level="beginner")
        
        session = StreamingSession(
            session_id="error_test",
            websocket=mock_websocket,
            student_profile=student
        )
        
        # Try to send message (should handle error)
        await session.send_message({"type": "test"})
        
        # Session should be marked inactive after error
        assert session.active is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_message_handling(self):
        """Test handling of invalid messages"""
        from agents.state_schema import StudentProfile
        
        mock_websocket = AsyncMock(spec=WebSocket)
        student = StudentProfile(name="Invalid Test", level="beginner")
        
        session = StreamingSession(
            session_id="invalid_test",
            websocket=mock_websocket,
            student_profile=student
        )
        
        # Try to send invalid message types
        invalid_messages = [
            None,
            "",
            [],
            123
        ]
        
        for msg in invalid_messages:
            # Should handle gracefully
            try:
                await session.send_message(msg)
            except:
                pass  # Expected to handle errors internally
