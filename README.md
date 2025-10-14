# Multi Agent Tutor

**An agentic AI that personalized learning on ANYTHING. Teach anyone anything using AI!**


```bash
# Run the AI tutor
python main_tutor.py

# Visit: http://localhost:8000
```

## Just some info on what it does (Or will do)

- Teaches any subject at any level
- Adapts to different learning styles
- Creates personalized lesson plans
- Generates practice problems
- Tracks learning progress

## Usage - (Api Request format)

```bash
# Teach math to a beginner
curl -X POST "http://localhost:8000/teach" \
  -d '{"topic": "basic algebra", "student_level": "beginner"}'

# Quick question answering
curl -X POST "http://localhost:8000/ask" \
  -d '{"question": "How does photosynthesis work?"}'
```
