# Changelog

All notable changes to the Multi-Agent Educational Tutoring System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.1.0] - 2025-10-18 - Phase 2 Complete

### Added - LLM Integration
- **Educational LLM Manager** (`src/llm/educational_clients.py`):
  - OpenAI GPT-4 integration for premium AI content
  - Ollama local model support for free AI alternative
  - Educational prompt templates for different subjects
  - Student personalization based on learning profile
  - Methods: `create_lesson_explanation()`, `generate_practice_problems()`, `assess_student_response()`
  - Automatic fallback from OpenAI → Ollama → Rule-based

### Added - Specialized Subject Agents
- **MathTutorAgent** (`src/agents/subject_experts.py`):
  - Step-by-step mathematical explanations
  - SymPy integration for symbolic math
  - Visualization suggestions for concepts
  - Example problem generation
- **ScienceTutorAgent**:
  - Physics, Chemistry, Biology explanations
  - Real-world application examples
  - Safe experiment suggestions
  - Concept-to-practice connections
- **ProgrammingTutorAgent**:
  - Multi-language code explanations
  - Working code example generation
  - Debugging assistance
  - Best practices and common pitfalls

### Added - Advanced RAG System
- **EducationalRAG** (`src/rag/educational_retrieval.py`):
  - ChromaDB vector database integration
  - Semantic search with sentence transformers
  - Keyword search with BM25
  - Hybrid search combining both approaches
  - Subject and level filtering
- **EducationalReranker**:
  - Cross-encoder re-ranking for relevance
  - Level-appropriate content filtering
  - Quality-based result sorting

### Added - Enhanced Orchestration
- **Smart routing by subject** in `tutoring_graph.py`:
  - Math topics → MathTutorAgent
  - Science topics → ScienceTutorAgent
  - Programming topics → ProgrammingTutorAgent
  - General topics → Standard pipeline
- **Feature flags** for flexible deployment:
  - `enable_llm` - Toggle LLM features
  - `enable_specialized_agents` - Toggle specialized agents
  - `enable_advanced_rag` - Toggle advanced RAG
- **Graceful degradation** - System works without Phase 2 features

### Added - Configuration
- Enhanced `.env` with Phase 2 settings:
  - `OPENAI_API_KEY` - OpenAI configuration
  - `USE_OPENAI` - Enable/disable OpenAI
  - `USE_OLLAMA` - Enable/disable Ollama
  - `OLLAMA_HOST` / `OLLAMA_MODEL` - Ollama settings
  - `USE_ADVANCED_RAG` - Enable/disable RAG
  - `USE_SPECIALIZED_AGENTS` - Enable/disable specialists
  - `CHROMA_PERSIST_DIR` - Vector DB location

### Added - Testing & Verification
- `tests/test_phase2_llm.py` - Comprehensive Phase 2 test suite:
  - LLM manager tests
  - Specialized agent tests
  - RAG system tests
  - Integration tests

### Added - Documentation
- Updated `README.md` with Phase 2 features
- Enhanced API documentation
- Configuration guide
- Setup instructions for OpenAI and Ollama

### Added - Dependencies
```
# Phase 2: LLM Integration
openai>=1.0.0           # OpenAI GPT-4
ollama>=0.1.0           # Local AI fallback

# Phase 2: Advanced RAG
chromadb>=0.4.15                 # Vector database
sentence-transformers>=2.2.2     # Embeddings & re-ranking
rank-bm25>=0.2.2                 # BM25 keyword search

# Phase 2: Educational Enhancement
sympy>=1.12              # Symbolic math for Math Tutor
matplotlib>=3.7.0        # Visualizations
plotly>=5.17.0          # Interactive charts
```

### Changed
- `tutoring_graph.py` - Integrated Phase 2 components with backward compatibility
- `educational_nodes.py` - Ready to accept LLM and RAG components
- `requirements.txt` - Added all Phase 2 dependencies
- `.env` - Enhanced with Phase 2 configuration options

### Technical Improvements
- Intelligent LLM fallback chain
- Async/await support throughout
- Vector search for content retrieval
- Cross-encoder re-ranking
- Subject-based agent routing
- Configurable deployment options
- Comprehensive error handling
- Production-ready logging

### Educational Quality Improvements
- AI-generated explanations adapt to student level
- Domain expertise through specialized agents
- Semantic understanding of learning requests
- Personalized content generation
- Higher quality practice problems
- Intelligent assessment feedback

---

## [2.0.0] - 2025-10-15 - Phase 1 Complete 

### Added - Multi-Agent Architecture
- **6 Specialized Educational Agents**:
  - `SubjectExpertAgent` - Subject detection and routing
  - `ContentCreatorAgent` - Personalized lesson plan generation
  - `ContentRetrieverAgent` - Educational resource discovery
  - `PracticeGeneratorAgent` - Adaptive practice problem creation
  - `AssessmentAgent` - Evaluation strategy development
  - `ProgressTrackerAgent` - Learning analytics and feedback

### Added - LangGraph Integration
- Complete LangGraph-based orchestration system
- Comprehensive state management with `TutoringState`
- Enhanced `StudentProfile` with learning goals and history
- Linear educational pipeline workflow
- Error handling and recovery mechanisms
- Agent coordination and communication

### Added - New API Endpoints
- `POST /teach/advanced` - Multi-agent teaching sessions
- `POST /practice/personalized` - Personalized practice generation
- `POST /assess/understanding` - Enhanced student assessment
- `GET /system-status` - Detailed system and agent status
- All endpoints return multi-agent metadata

### Added - Testing
- `tests/test_educational_system.py` - Complete test suite
- Unit tests for all state management components
- Integration tests for multi-agent workflows
- Backward compatibility tests
- Error handling and edge case tests

### Added - File Structure
```
src/agents/
├── state_schema.py          # State management
├── educational_nodes.py     # Agent node implementations
└── tutoring_graph.py        # LangGraph orchestration

tests/
└── test_educational_system.py  # Comprehensive tests

```

### Changed
- `main_tutor.py` - Enhanced with multi-agent endpoints
- `requirements.txt` - Added LangGraph and LangChain dependencies
- Welcome page now shows multi-agent system
- All responses include agent orchestration details

### Maintained - Backward Compatibility
- Original `/teach` endpoint preserved
- Original `/ask` endpoint preserved
- Original `/assess` endpoint preserved
- `UniversalAITutor` class unchanged
- All v1.0 functionality still works

### Technical Improvements
- Comprehensive error handling across all agents
- Detailed logging for debugging
- Session tracking and history
- Agent performance monitoring
- State serialization support

---

## [1.0.0] - 2024-XX-XX - Initial Release

### Added - Core Features
- Basic educational tutoring system
- `UniversalAITutor` class for teaching any subject
- Subject and level detection
- Learning style adaptation
- Practice problem generation
- Basic assessment capabilities

### Added - Educational Content
- DuckDuckGo web search integration
- Wikipedia content retrieval
- Lesson plan generation
- Educational explanations
- Rule-based content creation

### Added - API Framework
- FastAPI web service
- `/teach` endpoint for teaching sessions
- `/ask` endpoint for quick questions
- `/assess` endpoint for student assessment
- `/demo` endpoint for demonstrations
- `/subjects` endpoint for capability listing

### Added - Student Profiling
- `LearningProfile` dataclass
- Learning level tracking (beginner/intermediate/advanced)
- Learning style preferences (visual/auditory/kinesthetic/mixed)
- Subject mastery tracking
- Progress scoring

### Added - Documentation
- Basic README with usage examples
- API endpoint documentation
- Student guide
- Example lesson JSON

---

## [Unreleased] - Future Phases

### Phase 3: Production Features (Planned)
- WebSocket streaming for real-time sessions
- PostgreSQL database for persistence
- Redis caching for performance
- Educational analytics dashboard
- LangSmith monitoring integration
- Student data management
- Session history and replay

### Phase 4: Deployment & Optimization (Planned)
- Docker containerization
- docker-compose for multi-service deployment
- Production-ready configuration
- Load testing and optimization
- Comprehensive deployment documentation
- CI/CD pipeline
- Performance monitoring

---

