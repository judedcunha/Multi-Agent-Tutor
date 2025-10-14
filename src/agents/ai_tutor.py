# src/agents/ai_tutor.py
import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import wikipedia
from ddgs import DDGS
import re
import random
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LearningProfile:
    """Student's learning profile and progress"""
    name: str = "Student"
    level: str = "beginner"  # beginner, intermediate, advanced
    learning_style: str = "mixed"  # visual, auditory, kinesthetic, mixed
    subjects_learned: List[str] = None
    current_topic: str = ""
    progress_score: float = 0.0
    
    def __post_init__(self):
        if self.subjects_learned is None:
            self.subjects_learned = []

class UniversalAITutor:
    """
    Teaches any subject to any level
    """
    
    def __init__(self, use_local_model: bool = False):
        self.use_local_model = use_local_model
        self.model = None
        self.tokenizer = None
        self.ddg = DDGS()
        
        # Subject expertise mappings
        self.subject_keywords = {
            "math": ["mathematics", "algebra", "calculus", "geometry", "statistics"],
            "science": ["physics", "chemistry", "biology", "astronomy", "geology"],
            "programming": ["python", "javascript", "coding", "software", "algorithms"],
            "history": ["historical", "timeline", "civilization", "events", "culture"],
            "language": ["grammar", "vocabulary", "pronunciation", "linguistics"],
            "art": ["drawing", "painting", "design", "creativity", "visual"],
            "music": ["theory", "instruments", "composition", "rhythm", "melody"]
        }
        
        # Learning level definitions
        self.level_indicators = {
            "beginner": ["basic", "introduction", "fundamentals", "simple", "easy"],
            "intermediate": ["intermediate", "moderate", "standard", "typical"],
            "advanced": ["advanced", "complex", "expert", "sophisticated", "graduate"]
        }
        
        logger.info("Tutor ready")
    
    def detect_subject_and_level(self, topic: str) -> Dict[str, str]:
        """Detect what subject and level the student is asking about"""
        topic_lower = topic.lower()
        
        # Detect subject
        detected_subject = "general"
        confidence = 0
        
        for subject, keywords in self.subject_keywords.items():
            subject_confidence = sum(1 for keyword in keywords if keyword in topic_lower)
            if subject_confidence > confidence:
                confidence = subject_confidence
                detected_subject = subject
        
        # Detect level from topic complexity
        detected_level = "beginner"
        
        for level, indicators in self.level_indicators.items():
            if any(indicator in topic_lower for indicator in indicators):
                detected_level = level
                break
        
        # Advanced heuristics
        if any(word in topic_lower for word in ["how to", "what is", "explain", "basics"]):
            detected_level = "beginner"
        elif any(word in topic_lower for word in ["advanced", "deep dive", "complex", "theory"]):
            detected_level = "advanced"
        elif any(word in topic_lower for word in ["implement", "build", "create", "design"]):
            detected_level = "intermediate"
        
        return {
            "subject": detected_subject,
            "level": detected_level,
            "confidence": confidence
        }
    
    def find_educational_content(self, topic: str, subject: str, level: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Find educational content"""
        educational_sources = []
        
        # Create educational search queries
        search_queries = [
            f"{topic} tutorial {level}",
            f"learn {topic} {level}"
        ]
        
        # Search for educational content
        for query in search_queries[:1]:  # Limit to avoid rate limits
            try:
                results = list(self.ddg.text(
                    query,  
                    max_results=max_results
                ))
                
                for result in results:
                    educational_sources.append({
                        'title': result.get('title', ''),
                        'url': result.get('href', ''),
                        'content': result.get('body', ''),
                        'source_type': 'educational_web',
                        'subject': subject,
                        'estimated_level': level
                    })
                        
            except Exception as e:
                logger.warning(f"Educational search error: {e}")
                continue
        
        # Get Wikipedia educational content 
        try:
            wiki_results = self._get_wikipedia_educational(topic, subject)
            educational_sources.extend(wiki_results)
        except Exception as e:
            logger.warning(f"Wikipedia educational search error: {e}")
        
        return educational_sources[:max_results * 2]
    
    
    def _get_wikipedia_educational(self, topic: str, subject: str) -> List[Dict[str, Any]]:
        """Get educational content from Wikipedia"""
        try:
            search_results = wikipedia.search(topic, results=2)
            
            educational_content = []
            for title in search_results:
                try:
                    summary = wikipedia.summary(title, sentences=4)
                    page = wikipedia.page(title)
                    
                    educational_content.append({
                        'title': title,
                        'url': page.url,
                        'content': summary,
                        'source_type': 'educational_wiki',
                        'subject': subject,
                        'estimated_level': 'intermediate'
                    })
                    
                except (wikipedia.exceptions.DisambiguationError, 
                       wikipedia.exceptions.PageError):
                    continue
            
            return educational_content
            
        except Exception as e:
            logger.warning(f"Wikipedia educational error: {e}")
            return []
    
    def create_lesson_plan(self, topic: str, subject: str, level: str, 
                          learning_style: str = "mixed") -> Dict[str, Any]:
        """Create a structured lesson plan for the topic"""
        lesson_plan = {
            "topic": topic,
            "subject": subject,
            "level": level,
            "learning_style": learning_style,
            "estimated_duration": "30-60 minutes",
            "objectives": [],
            "lesson_structure": {},
            "activities": [],
            "assessment": {},
            "resources": []
        }
        
        # Create learning objectives based on level
        if level == "beginner":
            lesson_plan["objectives"] = [
                f"Understand the basic concepts of {topic}",
                f"Identify key terms related to {topic}",
                f"Apply simple examples of {topic}",
                "Build confidence in the subject area"
            ]
        elif level == "intermediate":
            lesson_plan["objectives"] = [
                f"Analyze different aspects of {topic}",
                f"Compare and contrast key concepts in {topic}",
                f"Apply {topic} to practical scenarios",
                "Develop problem-solving skills"
            ]
        else:  # advanced
            lesson_plan["objectives"] = [
                f"Synthesize complex ideas about {topic}",
                f"Evaluate different approaches to {topic}",
                f"Create original solutions using {topic}",
                "Master advanced applications"
            ]
        
        # Structure lesson based on learning style
        if learning_style == "visual":
            lesson_plan["lesson_structure"] = {
                "warm_up": "Visual overview and mind map (5 min)",
                "introduction": "Concept diagrams and charts (15 min)",
                "main_content": "Step-by-step visual examples (25 min)",
                "practice": "Visual problem solving (10 min)",
                "wrap_up": "Summary infographic (5 min)"
            }
        else:  # mixed or other
            lesson_plan["lesson_structure"] = {
                "warm_up": "Interactive introduction (5 min)",
                "introduction": "Multi-modal explanation (15 min)",
                "main_content": "Varied examples and practice (25 min)",
                "practice": "Choice of activities (10 min)",
                "wrap_up": "Flexible review (5 min)"
            }
        
        return lesson_plan
    
    def generate_explanation(self, topic: str, level: str, learning_style: str = "mixed") -> Dict[str, Any]:
        """Generate a clear, level-appropriate explanation"""
        explanation = {
            "topic": topic,
            "level": level,
            "learning_style": learning_style,
            "main_explanation": "",
            "key_points": [],
            "examples": [],
            "analogies": [],
            "common_misconceptions": [],
            "next_steps": []
        }
        
        explanation["main_explanation"] = self._generate_rule_based_explanation(topic, level)
        
        # Add level-appropriate key points
        if level == "beginner":
            explanation["key_points"] = [
                f"What is {topic}? (Definition and basics)",
                f"Why is {topic} important?",
                f"How does {topic} work in simple terms?",
                f"Common uses of {topic} in daily life"
            ]
        elif level == "intermediate":
            explanation["key_points"] = [
                f"Core principles behind {topic}",
                f"Different types or categories of {topic}",
                f"How {topic} connects to other concepts",
                f"Practical applications and examples"
            ]
        else:  # advanced
            explanation["key_points"] = [
                f"Advanced theories and models of {topic}",
                f"Current research and developments in {topic}",
                f"Complex applications and edge cases",
                f"Integration with other advanced concepts"
            ]
        
        # Generate examples based on topic
        explanation["examples"] = self._generate_examples(topic, level)
        
        # Create analogies for understanding
        explanation["analogies"] = self._generate_analogies(topic, level)
        
        return explanation
    
    def _generate_rule_based_explanation(self, topic: str, level: str) -> str:
        """Generate explanation using rule-based approach"""
        if level == "beginner":
            return f"""
Let me explain {topic} in simple terms:

{topic} is an important concept that helps us understand how things work. Think of it as a building block for learning more advanced ideas.

To understand {topic}, let's break it down:
1. What it is (the basic definition)
2. Why it matters (how it's useful)
3. How it works (the main process)  
4. Where you see it (real examples)

The key to learning {topic} is to start with the basics and build up your understanding step by step. Don't worry if it seems complex at first - everyone starts as a beginner!
"""
        elif level == "intermediate":
            return f"""
Now let's explore {topic} in more depth:

{topic} involves several interconnected concepts that work together. At this level, you should understand not just WHAT {topic} is, but HOW and WHY it works the way it does.

Key areas to focus on:
1. The underlying principles and mechanisms
2. Different variations or approaches
3. How it connects to related topics
4. Practical applications and problem-solving

Remember, intermediate learning is about making connections and seeing patterns. Look for relationships between {topic} and what you already know.
"""
        else:  # advanced
            return f"""
At the advanced level, {topic} requires sophisticated understanding:

{topic} represents a complex domain with multiple layers of depth. Advanced learners should be able to synthesize information, evaluate different approaches, and create novel applications.

Focus areas for mastery:
1. Theoretical foundations and current research
2. Complex interactions and edge cases
3. Integration with multiple other domains
4. Original problem-solving and innovation

Advanced learning means becoming comfortable with complexity and pushing the boundaries of current knowledge in {topic}.
"""
    
    def _generate_examples(self, topic: str, level: str) -> List[str]:
        """Generate relevant examples for the topic"""
        examples = [
            f"Example 1: A simple, everyday situation involving {topic}",
            f"Example 2: A step-by-step walkthrough of {topic} in action",
            f"Example 3: A common problem solved using {topic}"
        ]
        
        if level == "advanced":
            examples.append(f"Advanced Example: A complex real-world application of {topic}")
        
        return examples
    
    def _generate_analogies(self, topic: str, level: str) -> List[str]:
        """Generate helpful analogies for understanding"""
        analogies = [
            f"Think of {topic} like a familiar everyday activity",
            f"{topic} is similar to something you already understand"
        ]
        
        return analogies
    
    def create_practice_problems(self, topic: str, subject: str, level: str, count: int = 3) -> List[Dict[str, Any]]:
        """Create practice problems for the student"""
        problems = []
        
        for i in range(count):
            problem = {
                "id": f"{topic}_{level}_{i+1}",
                "question": f"Practice problem {i+1} about {topic}",
                "type": "open_ended",
                "level": level,
                "hints": [
                    f"Think about the key concepts of {topic}",
                    f"Remember what you learned about {topic}",
                    "Try working through this step by step"
                ],
                "solution_approach": f"To solve this problem, apply the principles of {topic} that we discussed",
                "estimated_time": "5-10 minutes"
            }
            problems.append(problem)
        
        return problems
    
    def assess_understanding(self, topic: str, student_response: str) -> Dict[str, Any]:
        """Assess student's understanding based on their response"""
        assessment = {
            "topic": topic,
            "understanding_level": "developing",
            "strengths": [],
            "areas_for_improvement": [],
            "next_steps": [],
            "confidence_score": 0.5
        }
        
        response_lower = student_response.lower()
        
        # Simple keyword-based assessment
        positive_indicators = ["understand", "clear", "makes sense", "got it", "i see"]
        confusion_indicators = ["confused", "don't understand", "unclear", "difficult", "hard"]
        
        positive_count = sum(1 for indicator in positive_indicators if indicator in response_lower)
        confusion_count = sum(1 for indicator in confusion_indicators if indicator in response_lower)
        
        if positive_count > confusion_count:
            assessment["understanding_level"] = "good"
            assessment["confidence_score"] = 0.7
            assessment["strengths"] = [
                "Shows positive engagement with the material",
                "Demonstrates comprehension of key concepts"
            ]
        elif confusion_count > 0:
            assessment["understanding_level"] = "needs_support"
            assessment["confidence_score"] = 0.3
            assessment["areas_for_improvement"] = [
                "Needs clearer explanations",
                "May benefit from different learning approach"
            ]
        
        return assessment
    
    def teach_topic(self, topic: str, student_profile: LearningProfile = None) -> Dict[str, Any]:
        """Main teaching method - comprehensive lesson on any topic"""
        if student_profile is None:
            student_profile = LearningProfile()
        
        logger.info(f"🎓 Teaching {topic} to {student_profile.level} student")
        
        # Detect subject and level
        topic_analysis = self.detect_subject_and_level(topic)
        
        # Use student's preferred level if available
        teaching_level = student_profile.level if student_profile.level != "beginner" else topic_analysis["level"]
        
        teaching_session = {
            "topic": topic,
            "student_profile": student_profile,
            "detected_subject": topic_analysis["subject"],
            "teaching_level": teaching_level,
            "timestamp": datetime.now().isoformat(),
            "lesson_plan": {},
            "explanation": {},
            "educational_content": [],
            "practice_problems": [],
            "assessment_ready": True,
            "cost": "0 bro"
        }
        
        # Find educational content
        educational_content = self.find_educational_content(
            topic, topic_analysis["subject"], teaching_level
        )
        teaching_session["educational_content"] = educational_content
        
        # Create lesson plan
        lesson_plan = self.create_lesson_plan(
            topic, topic_analysis["subject"], teaching_level, student_profile.learning_style
        )
        teaching_session["lesson_plan"] = lesson_plan
        
        # Generate explanation
        explanation = self.generate_explanation(
            topic, teaching_level, student_profile.learning_style
        )
        teaching_session["explanation"] = explanation
        
        # Create practice problems
        practice_problems = self.create_practice_problems(
            topic, topic_analysis["subject"], teaching_level
        )
        teaching_session["practice_problems"] = practice_problems
        
        # Update student profile
        if topic not in student_profile.subjects_learned:
            student_profile.subjects_learned.append(topic)
        student_profile.current_topic = topic
        
        logger.info(f"Teaching session completed for {topic} ")
        return teaching_session

def test_ai_tutor():
    """Test the ssytem"""
    print("Testing")
    print("=" * 50)
    
    tutor = UniversalAITutor(use_local_model=False)
    
    # Test with different subjects and levels
    test_cases = [
        ("Python programming basics", LearningProfile(level="beginner", learning_style="visual")),
        ("Basic algebra", LearningProfile(level="beginner", learning_style="mixed"))
    ]
    
    for topic, profile in test_cases[:1]:  # Test just one for speed
        print(f"\nTeaching: {topic}")
        print(f"Student: {profile.level} level, {profile.learning_style} style")
        
        session = tutor.teach_topic(topic, profile)
        
        print(f"Subject detected: {session['detected_subject']}")
        print(f"Teaching level: {session['teaching_level']}")
        print(f"Educational sources: {len(session['educational_content'])}")
        print(f"Practice problems: {len(session['practice_problems'])}")
        print(f"Cost: {session['cost']}")
    
    print("\n" + "=" * 50)
    print("AI Tutor testing completed!")
    return True

if __name__ == "__main__":
    test_ai_tutor()