"""
Comprehensive test suite for Phase 1: LangGraph Foundation
Tests all multi-agent functionality and backward compatibility
"""

import pytest
import sys
import os
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.tutoring_graph import AdvancedTutoringSystem
from agents.state_schema import StudentProfile, create_initial_state, TutoringState
from agents.ai_tutor import UniversalAITutor, LearningProfile


class TestStateManagement:
    """Test state schema and management"""
    
    def test_student_profile_creation(self):
        """Test StudentProfile creation and serialization"""
        profile = StudentProfile(
            name="Test Student",
            level="intermediate",
            learning_style="visual",
            learning_goals=["Learn Python", "Master algorithms"]
        )
        
        assert profile.name == "Test Student"
        assert profile.level == "intermediate"
        assert len(profile.learning_goals) == 2
        
        # Test serialization
        profile_dict = profile.to_dict()
        assert isinstance(profile_dict, dict)
        assert profile_dict["name"] == "Test Student"
        
        # Test deserialization
        restored = StudentProfile.from_dict(profile_dict)
        assert restored.name == profile.name
        assert restored.level == profile.level
    
    def test_initial_state_creation(self):
        """Test initial TutoringState creation"""
        profile = StudentProfile(name="Alice", level="beginner")
        state = create_initial_state(
            learning_request="Python basics",
            student_profile=profile,
            session_id="test-123"
        )
        
        assert state["learning_request"] == "Python basics"
        assert state["session_id"] == "test-123"
        assert state["current_agent"] == "start"
        assert state["next_agent"] == "subject_expert"
        assert isinstance(state["messages"], list)
        assert isinstance(state["agent_history"], list)


class TestBasicTutor:
    """Test backward compatibility with original tutor"""
    
    def test_basic_tutor_initialization(self):
        """Test UniversalAITutor initialization"""
        tutor = UniversalAITutor(use_local_model=False)
        assert tutor is not None
        assert tutor.ddg is not None
    
    def test_subject_detection(self):
        """Test subject and level detection"""
        tutor = UniversalAITutor(use_local_model=False)
        
        # Test math detection
        result = tutor.detect_subject_and_level("basic algebra equations")
        assert result["subject"] == "math"
        
        # Test programming detection
        result = tutor.detect_subject_and_level("python programming tutorial")
        assert result["subject"] == "programming"
    
    def test_basic_teaching_session(self):
        """Test basic teaching functionality"""
        tutor = UniversalAITutor(use_local_model=False)
        profile = LearningProfile(level="beginner", learning_style="visual")
        
        session = tutor.teach_topic("Python basics", profile)
        
        assert session["topic"] == "Python basics"
        assert "lesson_plan" in session
        assert "explanation" in session
        assert "practice_problems" in session
        assert len(session["practice_problems"]) > 0


class TestAdvancedSystem:
    """Test multi-agent advanced tutoring system"""
    
    def test_system_initialization(self):
        """Test AdvancedTutoringSystem initialization"""
        system = AdvancedTutoringSystem(use_local_model=False)
        
        assert system is not None
        assert system.tutor is not None
        assert system.nodes is not None
        assert system.graph is not None
        assert system.compiled_graph is not None
    
    def test_system_status(self):
        """Test system status reporting"""
        # Initialize with Phase 2 features explicitly disabled to test Phase 1 status
        system = AdvancedTutoringSystem(
            use_local_model=False,
            enable_llm=False,
            enable_specialized_agents=False,
            enable_advanced_rag=False
        )
        status = system.get_system_status()
        
        assert status["system"] == "Advanced Multi-Agent Tutoring System"
        assert status["phase"] == "Phase 1: LangGraph Foundation"
        assert status["agents"]["count"] == 6
        assert len(status["agents"]["active"]) == 6
        assert status["features"]["multi_agent_orchestration"] is True
    
    def test_graph_visualization(self):
        """Test graph visualization generation"""
        system = AdvancedTutoringSystem(use_local_model=False)
        viz = system.get_graph_visualization()
        
        assert isinstance(viz, str)
        assert "Subject Expert" in viz
        assert "Content Creator" in viz
        assert "Progress Tracker" in viz
    
    def test_multi_agent_teaching_session(self):
        """Test complete multi-agent teaching session"""
        system = AdvancedTutoringSystem(use_local_model=False)
        profile = StudentProfile(
            name="Test Student",
            level="beginner",
            learning_style="mixed"
        )
        
        session = system.teach_topic("Introduction to Python", profile)
        
        # Verify session structure
        assert session["topic"] == "Introduction to Python"
        assert session["multi_agent"] is True
        assert session["agent_count"] == 6
        assert len(session["agents_involved"]) == 6
        
        # Verify all agents were involved
        expected_agents = [
            "subject_expert",
            "content_creator",
            "content_retriever",
            "practice_generator",
            "assessment_agent",
            "progress_tracker"
        ]
        for agent in expected_agents:
            assert agent in session["agents_involved"]
        
        # Verify educational content
        assert "lesson_plan" in session
        assert "explanation" in session
        assert "educational_content" in session
        assert "practice_problems" in session
        assert "assessments" in session
        
        # Verify metadata
        assert "learning_progress" in session
        assert "session_feedback" in session
        assert session["learning_progress"]["completion_status"] == "completed"
    
    def test_different_learning_levels(self):
        """Test system with different learning levels"""
        system = AdvancedTutoringSystem(use_local_model=False)
        
        levels = ["beginner", "intermediate", "advanced"]
        
        for level in levels:
            profile = StudentProfile(level=level)
            session = system.teach_topic("Algebra basics", profile)
            
            assert session["teaching_level"] in levels
            assert session["multi_agent"] is True
            assert len(session["practice_problems"]) > 0
    
    def test_different_subjects(self):
        """Test system with different subjects"""
        system = AdvancedTutoringSystem(use_local_model=False)
        profile = StudentProfile(level="beginner")
        
        topics = [
            "Python programming",
            "Basic algebra",
            "Cell biology",
            "World War 2 history"
        ]
        
        for topic in topics:
            session = system.teach_topic(topic, profile)
            
            assert session["detected_subject"] is not None
            assert session["multi_agent"] is True
            assert len(session["agents_involved"]) == 6


class TestEducationalNodes:
    """Test individual educational nodes"""
    
    def test_subject_expert_node(self):
        """Test subject expert node"""
        system = AdvancedTutoringSystem(use_local_model=False)
        profile = StudentProfile(level="beginner")
        
        state = create_initial_state("Python basics", profile)
        result = system.nodes.subject_expert_node(state)
        
        assert result["detected_subject"] is not None
        assert result["detected_level"] is not None
        assert result["current_agent"] == "subject_expert"
        assert result["next_agent"] == "content_creator"
    
    def test_content_creator_node(self):
        """Test content creator node"""
        system = AdvancedTutoringSystem(use_local_model=False)
        profile = StudentProfile(level="beginner")
        
        state = create_initial_state("Python basics", profile)
        state["detected_subject"] = "programming"
        state["detected_level"] = "beginner"
        
        result = system.nodes.content_creator_node(state)
        
        assert "lesson_plan" in result
        assert "explanations" in result
        assert result["current_agent"] == "content_creator"
    
    def test_content_retriever_node(self):
        """Test content retriever node"""
        system = AdvancedTutoringSystem(use_local_model=False)
        profile = StudentProfile(level="beginner")
        
        state = create_initial_state("Python basics", profile)
        state["detected_subject"] = "programming"
        state["detected_level"] = "beginner"
        
        result = system.nodes.content_retriever_node(state)
        
        assert "educational_content" in result
        assert isinstance(result["educational_content"], list)
        assert result["current_agent"] == "content_retriever"
    
    def test_practice_generator_node(self):
        """Test practice generator node"""
        system = AdvancedTutoringSystem(use_local_model=False)
        profile = StudentProfile(level="beginner")
        
        state = create_initial_state("Python basics", profile)
        state["detected_subject"] = "programming"
        state["detected_level"] = "beginner"
        
        result = system.nodes.practice_generator_node(state)
        
        assert "practice_problems" in result
        assert len(result["practice_problems"]) > 0
        assert result["current_agent"] == "practice_generator"
    
    def test_assessment_agent_node(self):
        """Test assessment agent node"""
        system = AdvancedTutoringSystem(use_local_model=False)
        profile = StudentProfile(level="beginner")
        
        state = create_initial_state("Python basics", profile)
        state["detected_subject"] = "programming"
        state["detected_level"] = "beginner"
        
        result = system.nodes.assessment_agent_node(state)
        
        assert "assessments" in result
        assert len(result["assessments"]) > 0
        assert result["current_agent"] == "assessment_agent"
    
    def test_progress_tracker_node(self):
        """Test progress tracker node"""
        system = AdvancedTutoringSystem(use_local_model=False)
        profile = StudentProfile(level="beginner")
        
        state = create_initial_state("Python basics", profile)
        state["detected_subject"] = "programming"
        state["detected_level"] = "beginner"
        state["agent_history"] = ["subject_expert", "content_creator"]
        
        result = system.nodes.progress_tracker_node(state)
        
        assert "learning_progress" in result
        assert "session_feedback" in result
        assert result["current_agent"] == "progress_tracker"
        assert result["next_agent"] == "end"


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_empty_topic(self):
        """Test handling of empty topic"""
        system = AdvancedTutoringSystem(use_local_model=False)
        profile = StudentProfile(level="beginner")
        
        # Should handle gracefully
        session = system.teach_topic("", profile)
        assert session is not None
    
    def test_invalid_level(self):
        """Test handling of invalid learning level"""
        system = AdvancedTutoringSystem(use_local_model=False)
        profile = StudentProfile(level="invalid_level")
        
        # Should default to beginner or handle gracefully
        session = system.teach_topic("Python basics", profile)
        assert session is not None
    
    def test_node_error_recovery(self):
        """Test that errors in one node don't crash entire pipeline"""
        system = AdvancedTutoringSystem(use_local_model=False)
        profile = StudentProfile(level="beginner")
        
        # Even with errors, should complete
        session = system.teach_topic("Test topic", profile)
        assert session is not None
        assert "errors" in session


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_learning_workflow(self):
        """Test a complete learning workflow from start to finish"""
        system = AdvancedTutoringSystem(use_local_model=False)
        
        # Create student
        student = StudentProfile(
            name="Integration Test Student",
            level="intermediate",
            learning_style="visual",
            learning_goals=["Learn data structures"]
        )
        
        # Teaching session
        session = system.teach_topic("Binary trees in Python", student)
        
        # Verify complete workflow
        assert session["agent_count"] == 6
        assert session["learning_progress"]["completion_status"] == "completed"
        assert len(session["practice_problems"]) > 0
        assert len(session["educational_content"]) >= 0
        
        # Verify session quality
        assert session["session_feedback"]["overall_quality"] in ["high", "good"]
    
    def test_multiple_sessions_same_student(self):
        """Test multiple learning sessions for same student"""
        system = AdvancedTutoringSystem(use_local_model=False)
        student = StudentProfile(name="Multi-Session Student", level="beginner")
        
        topics = ["Python basics", "Python functions", "Python classes"]
        
        for topic in topics:
            session = system.teach_topic(topic, student)
            assert session["multi_agent"] is True
            assert session["topic"] == topic


def run_all_tests():
    """Run all tests with simple output"""
    print("\n" + "=" * 70)
    print("RUNNING PHASE 1 TESTS")
    print("=" * 70 + "\n")
    
    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])
    
    print("\n" + "=" * 70)
    print("TESTS COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_all_tests()
