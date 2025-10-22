"""
Phase 2 Testing Suite
Tests for LLM Integration, Specialized Agents, and Advanced RAG
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestPhase2LLM:
    """Test LLM Manager functionality"""
    
    @pytest.mark.asyncio
    async def test_llm_manager_initialization(self):
        """Test that LLM manager can be initialized"""
        try:
            from llm.educational_clients import create_llm_manager
            
            llm = create_llm_manager(use_openai=False, use_ollama=False)
            assert llm is not None
            print("LLM Manager initialization test passed")
        except ImportError:
            pytest.skip("Phase 2 LLM components not installed")
    
    @pytest.mark.asyncio
    async def test_lesson_explanation_generation(self):
        """Test LLM-generated lesson explanations"""
        try:
            from llm.educational_clients import create_llm_manager
            
            # Create manager first, then check if any provider is available
            llm = create_llm_manager()
            if not llm.use_openai and not llm.use_ollama:
                pytest.skip("No LLM service available (neither OpenAI nor Ollama)")
            
            explanation = await llm.create_lesson_explanation(
                topic="Python lists",
                level="beginner",
                learning_style="visual"
            )
            
            assert len(explanation) > 50
            assert 'list' in explanation.lower() or 'python' in explanation.lower()
            print("Lesson explanation generation test passed")
            
        except ImportError:
            pytest.skip("Phase 2 LLM components not installed")
    
    @pytest.mark.asyncio
    async def test_practice_problem_generation(self):
        """Test LLM-generated practice problems"""
        try:
            from llm.educational_clients import create_llm_manager
            
            # Create manager first, then check if any provider is available
            llm = create_llm_manager()
            if not llm.use_openai and not llm.use_ollama:
                pytest.skip("No LLM service available (neither OpenAI nor Ollama)")
            
            problems = await llm.generate_practice_problems(
                topic="Algebra equations",
                level="beginner",
                count=3
            )
            
            assert len(problems) >= 1  # At least one problem
            # Check that each problem has a non-empty 'text' field
            for problem in problems:
                assert 'text' in problem, f"Problem missing 'text' field: {problem}"
                assert isinstance(problem['text'], str), f"Problem 'text' is not a string: {problem}"
                assert len(problem['text'].strip()) > 0, f"Problem 'text' field is empty: {problem}"
            print("Practice problem generation test passed")
            
        except ImportError:
            pytest.skip("Phase 2 LLM components not installed")


class TestPhase2SpecializedAgents:
    """Test Specialized Subject Agents"""
    
    def test_specialized_agents_initialization(self):
        """Test that specialized agents can be created"""
        try:
            from agents.subject_experts import create_specialized_agents
            
            agents = create_specialized_agents(llm_manager=None)
            
            assert 'math_tutor' in agents
            assert 'science_tutor' in agents
            assert 'programming_tutor' in agents
            print("Specialized agents initialization test passed")
            
        except ImportError:
            pytest.skip("Phase 2 specialized agents not installed")
    
    @pytest.mark.asyncio
    async def test_math_tutor_explanation(self):
        """Test Math Tutor Agent"""
        try:
            from agents.subject_experts import MathTutorAgent
            
            math_tutor = MathTutorAgent(llm_manager=None)
            explanation = await math_tutor.explain_math_concept(
                concept="Algebra basics",
                level="beginner"
            )
            
            assert 'concept' in explanation
            assert 'main_explanation' in explanation
            assert len(explanation['main_explanation']) > 20
            print("Math tutor explanation test passed")
            
        except ImportError:
            pytest.skip("Phase 2 specialized agents not installed")
    
    @pytest.mark.asyncio
    async def test_science_tutor_explanation(self):
        """Test Science Tutor Agent"""
        try:
            from agents.subject_experts import ScienceTutorAgent
            
            science_tutor = ScienceTutorAgent(llm_manager=None)
            explanation = await science_tutor.explain_scientific_concept(
                concept="Photosynthesis",
                subject="biology",
                level="beginner"
            )
            
            assert 'concept' in explanation
            assert 'main_explanation' in explanation
            assert 'real_world_applications' in explanation
            print("Science tutor explanation test passed")
            
        except ImportError:
            pytest.skip("Phase 2 specialized agents not installed")
    
    @pytest.mark.asyncio
    async def test_programming_tutor_explanation(self):
        """Test Programming Tutor Agent"""
        try:
            from agents.subject_experts import ProgrammingTutorAgent
            
            prog_tutor = ProgrammingTutorAgent(llm_manager=None)
            explanation = await prog_tutor.explain_code_concept(
                language="Python",
                concept="functions",
                level="beginner"
            )
            
            assert 'language' in explanation
            assert 'concept' in explanation
            assert 'main_explanation' in explanation
            print("Programming tutor explanation test passed")
            
        except ImportError:
            pytest.skip("Phase 2 specialized agents not installed")


class TestPhase2RAG:
    """Test Advanced RAG System"""
    
    def test_rag_system_initialization(self):
        """Test RAG system can be initialized"""
        try:
            from rag.educational_retrieval import create_rag_system
            
            rag, reranker = create_rag_system()
            assert rag is not None
            assert reranker is not None
            print("RAG system initialization test passed")
            
        except ImportError:
            pytest.skip("Phase 2 RAG system not installed - install chromadb and sentence-transformers")
    
    @pytest.mark.asyncio
    async def test_rag_content_indexing(self):
        """Test indexing educational content"""
        try:
            from rag.educational_retrieval import create_rag_system
            
            rag, _ = create_rag_system()
            
            if not rag.initialized:
                pytest.skip("RAG system not fully initialized")
            
            sample_content = [
                {
                    'id': 'test_1',
                    'text': 'Python lists are ordered collections',
                    'metadata': {'subject': 'programming', 'level': 'beginner'}
                }
            ]
            
            success = await rag.index_educational_content(sample_content)
            assert success == True
            print("RAG content indexing test passed")
            
        except ImportError:
            pytest.skip("Phase 2 RAG system not installed")
    
    @pytest.mark.asyncio
    async def test_rag_content_retrieval(self):
        """Test retrieving educational content"""
        try:
            from rag.educational_retrieval import create_rag_system
            
            rag, _ = create_rag_system()
            
            if not rag.initialized:
                pytest.skip("RAG system not fully initialized")
            
            # Index sample content first
            sample_content = [
                {
                    'id': 'test_py_1',
                    'text': 'Python lists are ordered, mutable collections',
                    'metadata': {'subject': 'programming', 'level': 'beginner'}
                },
                {
                    'id': 'test_py_2',
                    'text': 'Python functions allow code reuse',
                    'metadata': {'subject': 'programming', 'level': 'beginner'}
                }
            ]
            
            await rag.index_educational_content(sample_content)
            
            # Try to retrieve
            results = await rag.retrieve_educational_content(
                query="What are Python lists?",
                subject="programming",
                student_level="beginner",
                top_k=2
            )
            
            assert isinstance(results, list)
            print(f"RAG content retrieval test passed - got {len(results)} results")
            
        except ImportError:
            pytest.skip("Phase 2 RAG system not installed")
    
    def test_reranker_functionality(self):
        """Test content reranking"""
        try:
            from rag.educational_retrieval import EducationalReranker
            
            reranker = EducationalReranker()
            
            if not reranker.initialized:
                pytest.skip("Reranker not fully initialized")
            
            candidates = [
                {'content': 'Python lists are great', 'score': 0.8},
                {'content': 'Python is a programming language', 'score': 0.7}
            ]
            
            reranked = reranker.rerank_for_learning(
                candidates,
                query="Python lists",
                student_level="beginner"
            )
            
            assert len(reranked) <= len(candidates)
            print("Reranker functionality test passed")
            
        except ImportError:
            pytest.skip("Phase 2 RAG system not installed")


class TestPhase2Integration:
    """Test integrated Phase 2 features"""
    
    def test_advanced_tutoring_system_phase2(self):
        """Test that Advanced Tutoring System initializes with Phase 2 features"""
        try:
            from agents.tutoring_graph import AdvancedTutoringSystem
            
            system = AdvancedTutoringSystem(
                use_local_model=False,
                enable_llm=False,  # Disabled for testing
                enable_specialized_agents=True,
                enable_advanced_rag=False  # Disabled for testing
            )
            
            assert system is not None
            
            # Get system status and check feature flags
            status = system.get_system_status()
            assert 'phase' in status, "Status missing 'phase' field"
            assert 'features' in status, "Status missing 'features' field"
            
            # Check that features dict contains expected flags
            features = status['features']
            assert 'llm_manager' in features, "Features missing 'llm_manager' flag"
            assert 'specialized_agents' in features, "Features missing 'specialized_agents' flag"
            assert 'rag_system' in features, "Features missing 'rag_system' flag"
            
            # Verify expected states based on initialization parameters
            assert features['llm_manager'] == False, "LLM manager should be disabled"
            assert features['specialized_agents'] == True, "Specialized agents should be enabled"
            assert features['rag_system'] == False, "RAG system should be disabled"
            
            print("Advanced tutoring system Phase 2 integration test passed")
            
        except ImportError as e:
            pytest.skip(f"Phase 2 components not fully installed: {e}")


def run_phase2_tests():
    """Run all Phase 2 tests"""
    print("\n" + "=" * 70)
    print("RUNNING PHASE 2 TEST SUITE")
    print("=" * 70 + "\n")
    
    # Run with pytest
    pytest.main([
        __file__,
        '-v',
        '-s',
        '--tb=short'
    ])


if __name__ == "__main__":
    run_phase2_tests()
