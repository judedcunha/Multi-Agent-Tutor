"""
Tests for core agent functionality including educational system, tutoring graph, and AI tutor
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from typing import Dict, Any

# Project imports - using actual module names
from agents.tutoring_graph import AdvancedTutoringSystem
from agents.state_schema import StudentProfile, TutoringState, create_initial_state
from agents.ai_tutor import UniversalAITutor
from agents.educational_nodes import EducationalNodes
from agents.subject_experts import MathTutorAgent, ScienceTutorAgent, ProgrammingTutorAgent


class TestStudentProfile:
    """Test suite for StudentProfile functionality"""
    
    @pytest.mark.unit
    def test_profile_creation(self):
        """Test StudentProfile creation with all fields"""
        profile = StudentProfile(
            name="Test Student",
            level="intermediate",
            learning_style="visual",
            learning_goals=["Learn Python", "Master algorithms"],
        )
        
        assert profile.name == "Test Student"
        assert profile.level == "intermediate"
        assert profile.learning_style == "visual"
        assert len(profile.learning_goals) == 2
        assert "Learn Python" in profile.learning_goals
        assert "Master algorithms" in profile.learning_goals
    
    @pytest.mark.unit
    def test_profile_serialization(self):
        """Test StudentProfile serialization and deserialization"""
        profile = StudentProfile(
            name="Alice",
            level="beginner",
            learning_style="kinesthetic"
        )
        
        # Serialize to dict
        profile_dict = profile.to_dict()
        assert isinstance(profile_dict, dict)
        assert profile_dict["name"] == "Alice"
        assert profile_dict["level"] == "beginner"
        
        # Deserialize from dict
        restored = StudentProfile.from_dict(profile_dict)
        assert restored.name == profile.name
        assert restored.level == profile.level
        assert restored.learning_style == profile.learning_style


class TestTutoringState:
    """Test suite for TutoringState management"""
    
    @pytest.mark.unit
    def test_initial_state_creation(self, sample_student_profile):
        """Test creation of initial tutoring state"""
        state = create_initial_state(
            learning_request="Python decorators",
            student_profile=sample_student_profile,
        )
        
        assert state["learning_request"] == "Python decorators"
        assert state["student_profile"] == sample_student_profile.to_dict()
        assert "messages" in state
        assert "current_agent" in state
    
    @pytest.mark.unit
    def test_state_update(self, sample_tutoring_state):
        """Test updating tutoring state fields"""
        # Update lesson plan (TutoringState is a dict, use bracket notation)
        sample_tutoring_state["lesson_plan"] = {
            "topics": ["decorators", "functions"],
            "duration": 30
        }
        
        assert sample_tutoring_state["lesson_plan"] is not None
        assert len(sample_tutoring_state["lesson_plan"]["topics"]) == 2


class TestAdvancedTutoringSystem:
    """Test suite for the AdvancedTutoringSystem"""
    
    @pytest.fixture(autouse=True)
    def setup(self, mock_llm):
        """Setup test instance with mocked dependencies"""
        with patch('llm.educational_clients.EducationalLLMManager') as mock_llm_class:
            mock_llm_class.return_value = mock_llm
            self.system = AdvancedTutoringSystem(use_local_model=False)
            self.student = StudentProfile(
                name="Test Student",
                level="intermediate"
            )
    
    @pytest.mark.unit
    def test_system_initialization(self):
        """Test tutoring system initialization"""
        assert self.system is not None
        assert hasattr(self.system, 'use_local_model')


class TestSubjectExperts:
    """Test suite for subject expert agents"""
    
    @pytest.mark.unit
    def test_math_tutor_agent(self):
        """Test MathTutorAgent initialization"""
        agent = MathTutorAgent()
        assert agent is not None
        assert hasattr(agent, 'llm')
    
    @pytest.mark.unit
    def test_science_tutor_agent(self):
        """Test ScienceTutorAgent initialization"""
        agent = ScienceTutorAgent()
        assert agent is not None
        assert hasattr(agent, 'llm')
    
    @pytest.mark.unit
    def test_programming_tutor_agent(self):
        """Test ProgrammingTutorAgent initialization"""
        agent = ProgrammingTutorAgent()
        assert agent is not None
        assert hasattr(agent, 'llm')
