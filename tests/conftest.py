"""
Shared test fixtures and configuration for Multi-Agent Tutor test suite
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import asyncio
from typing import Generator, Dict, Any
import redis
import os

# Setup project paths properly
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

# Import after path setup
from agents.state_schema import create_initial_state

# ============================================================================
# Service Availability Checks
# ============================================================================

def check_redis() -> bool:
    """Check if Redis is available"""
    try:
        r = redis.from_url('redis://localhost:6379/0')
        r.ping()
        return True
    except (redis.ConnectionError, Exception):
        return False


def check_ollama() -> bool:
    """Check if Ollama service is available"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=1)
        return response.status_code == 200
    except:
        return False


def check_chromadb() -> bool:
    """Check if ChromaDB is available"""
    try:
        import chromadb
        client = chromadb.Client()
        client.list_collections()
        return True
    except:
        return False


def check_langsmith() -> bool:
    """Check if LangSmith API is configured"""
    return bool(os.getenv('LANGCHAIN_API_KEY'))


def check_dependencies() -> Dict[str, bool]:
    """Check all service dependencies"""
    return {
        'redis': check_redis(),
        'ollama': check_ollama(),
        'chromadb': check_chromadb(),
        'langsmith': check_langsmith()
    }

# ============================================================================
# Session-scoped Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Get project root directory"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def temp_test_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files"""
    temp_dir = tempfile.mkdtemp(prefix="test_multi_agent_")
    temp_path = Path(temp_dir)
    yield temp_path
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_llm():
    """Mock LLM for testing without API calls"""
    llm = Mock()
    
    # Basic LLM methods
    llm.create_lesson_explanation = AsyncMock(return_value="This is a test lesson explanation")
    llm.generate_practice_problems = AsyncMock(return_value=[
        {"problem": "Test problem 1", "solution": "Solution 1"},
        {"problem": "Test problem 2", "solution": "Solution 2"}
    ])
    llm.evaluate_answer = AsyncMock(return_value={
        "score": 0.8,
        "feedback": "Good answer, but could be more detailed"
    })
    llm.generate_summary = AsyncMock(return_value="Test summary of the content")
    
    # Sync methods
    llm.invoke = Mock(return_value={"content": "Response"})
    
    return llm


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager for testing"""
    cache = Mock()
    cache.get.return_value = None  # Default to cache miss
    cache.set.return_value = True
    cache.delete.return_value = True
    cache.clear.return_value = True
    cache.exists.return_value = False
    cache.get_statistics.return_value = {
        "hits": 0,
        "misses": 0,
        "hit_ratio": 0.0
    }
    return cache


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    client = Mock()
    client.get.return_value = None
    client.set.return_value = True
    client.setex.return_value = True
    client.delete.return_value = 1
    client.exists.return_value = 0
    client.expire.return_value = True
    client.ttl.return_value = -2
    client.ping.return_value = True
    client.keys.return_value = []
    return client

# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def test_database():
    """In-memory SQLite database for testing"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    
    # Import Base and create tables
    try:
        from database.educational_models import Base
        Base.metadata.create_all(engine)
    except ImportError:
        # If models not available, skip database setup
        pass
    
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    
    yield session
    
    session.close()
    engine.dispose()


@pytest.fixture
def mock_chromadb_collection():
    """Mock ChromaDB collection"""
    collection = Mock()
    collection.add.return_value = None
    collection.query.return_value = {
        "documents": [["Test document 1", "Test document 2"]],
        "metadatas": [[{"source": "test1"}, {"source": "test2"}]],
        "distances": [[0.1, 0.2]]
    }
    collection.get.return_value = {
        "documents": ["Test document"],
        "metadatas": [{"source": "test"}]
    }
    collection.delete.return_value = None
    return collection

# ============================================================================
# Agent and System Fixtures
# ============================================================================

@pytest.fixture
def sample_student_profile():
    """Sample student profile for testing"""
    from agents.state_schema import StudentProfile
    
    return StudentProfile(
        name="Test Student",
        level="intermediate",
        learning_style="visual",
        learning_goals=["Learn Python", "Master algorithms"],
        subjects_mastered=["mathematics"],
        current_topic="Python"
    )


@pytest.fixture
def sample_tutoring_state(sample_student_profile):
    """Sample tutoring state for testing"""
    return create_initial_state(
        learning_request="Teach me about Python decorators",
        student_profile=sample_student_profile
    )

# ============================================================================
# WebSocket and API Fixtures
# ============================================================================

@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection"""
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_json = AsyncMock(return_value={"type": "test", "data": {}})
    ws.close = AsyncMock()
    ws.closed = False
    return ws


@pytest.fixture
def api_client():
    """Test client for FastAPI application"""
    try:
        from fastapi.testclient import TestClient
        from api.websocket_routes import app
        return TestClient(app)
    except ImportError:
        return None

# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_lesson_content():
    """Sample lesson content for testing"""
    return {
        "title": "Introduction to Python Decorators",
        "objectives": [
            "Understand what decorators are",
            "Learn how to create decorators",
            "Apply decorators in practice"
        ],
        "content": "Decorators are a powerful feature in Python...",
        "examples": [
            {"code": "@decorator\ndef function(): pass", "explanation": "Basic decorator syntax"}
        ],
        "summary": "Decorators allow you to modify function behavior"
    }


@pytest.fixture
def sample_rag_documents():
    """Sample documents for RAG testing"""
    return [
        {
            "content": "Python is a high-level programming language.",
            "metadata": {"source": "intro.md", "topic": "python"}
        },
        {
            "content": "Functions are reusable blocks of code.",
            "metadata": {"source": "functions.md", "topic": "python"}
        },
        {
            "content": "Object-oriented programming uses classes and objects.",
            "metadata": {"source": "oop.md", "topic": "python"}
        }
    ]

# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (may require services)")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_redis: Test requires Redis service")
    config.addinivalue_line("markers", "requires_llm: Test requires LLM service (Ollama)")
    config.addinivalue_line("markers", "requires_chromadb: Test requires ChromaDB")
    config.addinivalue_line("markers", "requires_langsmith: Test requires LangSmith API")
    config.addinivalue_line("markers", "performance: Performance benchmarks")
    config.addinivalue_line("markers", "asyncio: Async tests")


def pytest_collection_modifyitems(config, items):
    """Automatically add asyncio marker to async tests"""
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


def pytest_runtest_setup(item):
    """Skip tests based on service availability"""
    markers = {marker.name for marker in item.iter_markers()}
    
    if 'requires_redis' in markers and not check_redis():
        pytest.skip("Redis service not available")
    
    if 'requires_llm' in markers and not check_ollama():
        pytest.skip("Ollama LLM service not available")
    
    if 'requires_chromadb' in markers and not check_chromadb():
        pytest.skip("ChromaDB service not available")
    
    if 'requires_langsmith' in markers and not check_langsmith():
        pytest.skip("LangSmith API not configured")


# ============================================================================
# Utility Functions for Tests
# ============================================================================

def assert_valid_response(response: Dict[str, Any], required_fields: list):
    """Helper to validate API responses"""
    assert response is not None
    for field in required_fields:
        assert field in response, f"Missing required field: {field}"


def create_test_file(directory: Path, filename: str, content: str) -> Path:
    """Helper to create test files"""
    file_path = directory / filename
    file_path.write_text(content)
    return file_path


async def async_test_helper(coro):
    """Helper for running async tests"""
    return await coro
