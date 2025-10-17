# Multi-Agent Educational Tutoring System(WIP)

**An agentic AI platform that personalizes learning on ANY topic. Powered by LangGraph orchestration with 6 specialized educational agents.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)]()
[![LangGraph](https://img.shields.io/badge/LangGraph-0.0.40+-purple.svg)]()

---


### Multi-Agent Architecture
- **6 Specialized Educational Agents** working in coordination
- **LangGraph Orchestration** for intelligent agent coordination
- **Subject-Aware Routing** 
- **Comprehensive State Management** across all agents
- **Enhanced Learning Progress Tracking**

### Active Agents
```
Subject Expert → Content Creator → Content Retriever → 
Practice Generator → Assessment Agent → Progress Tracker
```

---

## Features

### Core Capabilities
- **Universal Teaching**: Any subject at any level (K-12 through Graduate)
- **Multi-Agent Coordination**: Specialized agents collaborate on each lesson
- **Personalized Learning**: Adapts to student level and learning style
- **Practice Generation**: Creates adaptive practice problems
- **Progress Tracking**: Comprehensive learning analytics
- **Educational Content**: Finds and curates relevant resources

### Learning Styles Supported
- **Visual**: Diagrams, charts, and visual explanations
- **Auditory**: Discussion-based and verbal learning
- **Kinesthetic**: Hands-on and practical activities
- **Mixed**: Combination of all approaches

### Subjects Covered
**STEM**: Math, Physics, Chemistry, Biology, Computer Science, Engineering  
**Languages**: English, Spanish, French, German, Mandarin, Programming Languages  
**Social Studies**: History, Geography, Psychology, Economics  
**Arts**: Art, Music, Literature, Creative Writing  
**Skills**: Study Skills, Test Prep, Critical Thinking, Problem Solving  

---

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Start

```bash
# Clone the repository
git clone https://github.com/judedcunha/Multi-Agent-Tutor
cd Multi-Agent-Tutor

# Install dependencies
pip install -r requirements.txt

# Start the server
cd src
python main_tutor.py
```

### Access the System
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **System Status**: http://localhost:8000/system-status

---

### Usage

### API Endpoints

#### Multi-Agent Teaching /
```bash
curl -X POST "http://localhost:8000/teach/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python programming basics",
    "student_level": "beginner",
    "learning_style": "visual",
    "student_name": "Alice",
    "learning_goals": ["Learn Python fundamentals"]
  }'
```

#### Personalized Practice
```bash
curl -X POST "http://localhost:8000/practice/personalized" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Algebra equations",
    "student_level": "intermediate"
  }'
```

#### Understanding Assessment
```bash
curl -X POST "http://localhost:8000/assess/understanding" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python loops",
    "student_response": "I understand how for loops work",
    "original_question": "Explain for loops"
  }'
```

#### System Status
```bash
curl http://localhost:8000/system-status
```

### Python SDK

```python
from agents.tutoring_graph import AdvancedTutoringSystem
from agents.state_schema import StudentProfile

# Initialize system
system = AdvancedTutoringSystem()

# Create student profile
student = StudentProfile(
    name="Alice",
    level="beginner",
    learning_style="visual",
    learning_goals=["Learn Python", "Build projects"]
)

# Teach a topic
session = system.teach_topic("Python basics", student)

# Access results
print(f"Agents involved: {session['agents_involved']}")
print(f"Practice problems: {len(session['practice_problems'])}")
print(f"Lesson objectives: {session['lesson_plan']['objectives']}")
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Application Layer                   │
│       /teach/advanced | /practice | /assess                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│         AdvancedTutoringSystem (LangGraph)                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │               Multi-Agent Graph                     │    │
│  │                                                     │    │
│  │   Subject Expert                                   │    │
│  │         ↓                                          │    │
│  │   Content Creator                                  │    │
│  │         ↓                                          │    │
│  │   Content Retriever                                │    │
│  │         ↓                                          │    │
│  │   Practice Generator                               │    │
│  │         ↓                                          │    │
│  │   Assessment Agent                                 │    │
│  │         ↓                                          │    │
│  │   Progress Tracker                                 │    │
│  │                                                     │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│            UniversalAITutor (Base Layer)                     │
│   Subject Detection | Content | Search | Assessment         │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Status
### (I will add this in the future) LLM Integration & Educational AI 
- [ ] OpenAI GPT-4 integration
- [ ] Specialized subject agents (Math/Science/Programming)
- [ ] Advanced RAG with ChromaDB
- [ ] Cross-encoder re-ranking
- [ ] Educational prompt templates

### Production Features (Future)
- [ ] WebSocket streaming
- [ ] PostgreSQL persistence
- [ ] Redis caching
- [ ] Educational analytics dashboard
- [ ] LangSmith monitoring

### Deployment & Optimization (Future)
- [ ] Docker deployment
- [ ] Load testing
- [ ] Performance optimization
- [ ] Comprehensive documentation

---

## Testing

### Verify Installation
```bash
# Quick verification
python verify_phase1.py
```

### Run Full Test Suite
```bash
cd tests
python test_educational_system.py

# Or with pytest
pytest test_educational_system.py -v
```

### Expected Results
- ✅ All state management tests pass
- ✅ All basic tutor tests pass
- ✅ All multi-agent tests pass
- ✅ All integration tests pass
- ✅ 6 agents working in coordination

---

## 📖 Documentation

- **Student Guide**: http://localhost:8000/student-guide
- **Supported Subjects**: http://localhost:8000/subjects
- **API Documentation**: http://localhost:8000/docs


---

## Example Use Cases

### For Students
```python
# Learn a new programming concept
session = system.teach_topic("Python list comprehensions", student)

# Get practice problems
problems = session['practice_problems']

# Review explanations
explanation = session['explanation']['main_explanation']
```

### For Educators
```python
# Create lesson plans
lesson_plan = session['lesson_plan']

# Track student progress
progress = session['learning_progress']

# Get assessment recommendations
feedback = session['session_feedback']
```

### For Researchers
```python
# Analyze multi-agent coordination
agents_used = session['agents_involved']
agent_count = session['agent_count']

# Study learning effectiveness
completion_status = session['learning_progress']['completion_status']
```

---

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```bash
# Basic Configuration
LOG_LEVEL=INFO
SERVER_PORT=8000

# LLM Configuration (Coming Soon)
# OPENAI_API_KEY=your_key_here
# OPENAI_MODEL=gpt-4-turbo-preview

# Database Configuration (Coming Soon)
# DATABASE_URL=postgresql://user:pass@localhost/tutor_db
# REDIS_URL=redis://localhost:6379
```

---


## Version History

### v2.0.0 - Phase 1 Complete (Current)
- Multi-agent architecture with LangGraph
- 6 specialized educational agents
- Enhanced API endpoints
- Comprehensive state management
- Complete test coverage

### v1.0.0 - Initial Release
- Basic educational tutoring
- Rule-based content generation
- Simple web search
- FastAPI endpoints

---

## License

MIT License - See LICENSE file for details

---


## My Educational Philosophy

This system is built on modern educational principles:
- **Personalization**: Every student learns differently
- **Active Learning**: Practice and engagement matter
- **Scaffolding**: Build on existing knowledge
- **Feedback**: Continuous assessment and adaptation
- **Multi-modal**: Support different learning styles

---

## Quick Commands

```bash
# Start server
cd src && python main_tutor.py

# Run tests
cd tests && python test_educational_system.py

# Check system status
curl http://localhost:8000/system-status

# Try a demo
curl http://localhost:8000/demo
```

---

**Teach anyone anything!**