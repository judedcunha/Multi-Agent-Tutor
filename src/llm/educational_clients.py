"""
Educational LLM Manager 
Handles LLM-based content generation with OpenAI OR Ollama 
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Educational Prompt Templates
LESSON_EXPLANATION_TEMPLATE = """You are an expert educational tutor. Create a comprehensive lesson explanation.

Topic: {topic}
Student Level: {level}
Learning Style: {learning_style}
Student Background: {student_context}

Create a {level}-level explanation that:
1. Introduces the concept clearly with appropriate context
2. Provides detailed explanation with relevant examples
3. Includes real-world applications and practical uses
4. Adapts to the {learning_style} learning style
5. Uses encouraging language to engage and motivate the student

For visual learners: Include descriptions of diagrams, charts, or visual representations
For auditory learners: Structure as a verbal explanation with discussion points
For kinesthetic learners: Include hands-on activities and practical exercises
For mixed learners: Combine multiple approaches

Explanation:"""

PRACTICE_PROBLEM_TEMPLATE = """You are creating educational practice problems for a student.

Topic: {topic}
Level: {level}
Number of Problems: {count}
Progressive Difficulty: {progressive}

Create {count} practice problems that:
- Test understanding of {topic}
- Are appropriate for {level} level
- Include clear problem statements
- Provide hints for solving (not full solutions)
- Progress in difficulty if progressive=True

Format each problem as:
Problem N: [Clear problem statement]
Hint: [Helpful hint without giving away the answer]
Difficulty: [Easy/Medium/Hard]

Problems:"""

ASSESSMENT_TEMPLATE = """You are evaluating a student's response to understand their comprehension.

Topic: {topic}
Original Question: {question}
Student's Answer: {student_answer}
Correct Answer (if provided): {correct_answer}

Provide a thoughtful assessment that:
1. Acknowledges what the student got right
2. Identifies any misconceptions or gaps
3. Provides constructive feedback
4. Suggests specific areas for improvement
5. Offers encouragement and next steps

Keep the tone positive and educational, not judgmental.

Assessment:"""

# Specialized Subject Templates
MATH_TUTOR_TEMPLATE = """You are a mathematics tutor specializing in clear, step-by-step explanations.

Topic: {topic}
Level: {level}
Student Question: {question}

Provide a mathematical explanation that:
1. States the key concept or formula clearly
2. Shows step-by-step solution process
3. Explains the reasoning behind each step
4. Provides visual descriptions where helpful (graphs, diagrams)
5. Includes practice tips and common mistakes to avoid

For {level} level, adjust complexity appropriately.

Explanation:"""

SCIENCE_TUTOR_TEMPLATE = """You are a science tutor who makes complex concepts accessible.

Topic: {topic}
Subject Area: {subject}
Level: {level}
Student Question: {question}

Provide a scientific explanation that:
1. Explains the core scientific principle
2. Uses appropriate analogies and real-world examples
3. Describes any relevant experiments or observations
4. Connects to practical applications
5. Addresses common misconceptions

Adjust complexity for {level} level students.

Explanation:"""

PROGRAMMING_TUTOR_TEMPLATE = """You are a programming tutor who teaches code concepts clearly.

Programming Language: {language}
Concept: {concept}
Level: {level}
Student Question: {question}

Provide a programming explanation that:
1. Explains the concept in plain language first
2. Shows clear, working code examples
3. Explains each line of important code
4. Provides practical use cases
5. Suggests debugging tips and best practices

Code examples should be:
- Clean and well-commented
- Appropriate for {level} level
- Runnable and correct
- Following best practices for {language}

Explanation:"""


class EducationalLLMManager:
    """
    Manages LLM-based educational content generation
    Uses OpenAI GPT-4 as primary, Ollama as fallback
    """
    
    def __init__(
        self, 
        use_openai: bool = True,
        openai_api_key: Optional[str] = None,
        openai_model: str = "gpt-4-turbo-preview",
        use_ollama: bool = True,
        ollama_host: str = "http://localhost:11434",
        ollama_model: str = "llama2"
    ):
        """
        Initialize Educational LLM Manager
        
        Args:
            use_openai: Whether to use OpenAI (requires API key)
            openai_api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            openai_model: OpenAI model to use
            use_ollama: Whether to use Ollama as fallback
            ollama_host: Ollama server URL
            ollama_model: Ollama model to use
        """
        self.use_openai = use_openai
        self.use_ollama = use_ollama
        self.openai_model = openai_model
        self.ollama_host = ollama_host
        self.ollama_model = ollama_model
        
        # Initialize OpenAI if enabled
        self.openai_client = None
        if use_openai:
            try:
                from openai import OpenAI
                api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
                if api_key and api_key != 'your_key_here':
                    self.openai_client = OpenAI(api_key=api_key)
                    logger.info(f"OpenAI client initialized with model: {openai_model}")
                else:
                    logger.warning("OpenAI API key not found - OpenAI will not be available")
                    self.use_openai = False
            except ImportError:
                logger.warning("OpenAI library not installed - install with: pip install openai")
                self.use_openai = False
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
                self.use_openai = False
        
        # Initialize Ollama if enabled
        self.ollama_client = None
        if use_ollama:
            try:
                import ollama
                self.ollama_client = ollama
                logger.info(f"Ollama client initialized with model: {ollama_model}")
            except ImportError:
                logger.warning("Ollama library not installed - install with: pip install ollama")
                self.use_ollama = False
            except Exception as e:
                logger.error(f"Failed to initialize Ollama: {e}")
                self.use_ollama = False
        
        logger.info(f"LLM Manager initialized - OpenAI: {self.use_openai}, Ollama: {self.use_ollama}")
    
    async def generate_content(
        self, 
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> str:
        """
        Generate content using available LLM
        
        Args:
            prompt: The prompt to send to the LLM
            temperature: Creativity level (0.0-1.0)
            max_tokens: Maximum response length
            
        Returns:
            Generated content as string
        """
        # Try OpenAI first
        if self.use_openai and self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": "You are an expert educational tutor."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                content = response.choices[0].message.content
                logger.info(f"Generated content using OpenAI ({len(content)} chars)")
                return content
            except Exception as e:
                logger.error(f"OpenAI generation failed: {e}")
                # Fall through to Ollama
        
        # Try Ollama as fallback
        if self.use_ollama and self.ollama_client:
            try:
                response = self.ollama_client.generate(
                    model=self.ollama_model,
                    prompt=prompt,
                    options={
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                )
                content = response['response']
                logger.info(f"Generated content using Ollama ({len(content)} chars)")
                return content
            except Exception as e:
                logger.error(f"Ollama generation failed: {e}")
                # Fall through to error
        
        # If both failed, return error message
        logger.error("All LLM providers failed - returning fallback message")
        return self._generate_fallback_content(prompt)
    
    def _generate_fallback_content(self, prompt: str) -> str:
        """Generate basic fallback content when LLMs unavailable"""
        return """**LLM Service Unavailable**

The AI tutoring service is currently unavailable. Please try:
1. Setting up an OpenAI API key in your .env file
2. Installing and running Ollama locally
3. Using the rule-based content generation (Phase 1)

For help, see the documentation or contact support."""
    
    async def create_lesson_explanation(
        self,
        topic: str,
        level: str = "beginner",
        learning_style: str = "mixed",
        student_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a comprehensive lesson explanation
        
        Args:
            topic: The topic to explain
            level: Student level (beginner/intermediate/advanced)
            learning_style: Preferred learning style
            student_context: Additional context about the student
            
        Returns:
            Comprehensive explanation as string
        """
        logger.info(f"Creating lesson explanation for: {topic} (level: {level})")
        
        context_str = ""
        if student_context:
            context_str = f"Student has background in: {', '.join(student_context.get('prior_knowledge', []))}"
        
        prompt = LESSON_EXPLANATION_TEMPLATE.format(
            topic=topic,
            level=level,
            learning_style=learning_style,
            student_context=context_str or "No prior knowledge specified"
        )
        
        return await self.generate_content(prompt, temperature=0.7, max_tokens=1500)
    
    async def generate_practice_problems(
        self,
        topic: str,
        level: str = "beginner",
        count: int = 5,
        difficulty_progression: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate practice problems for a topic
        
        Args:
            topic: The topic to create problems for
            level: Difficulty level
            count: Number of problems to generate
            difficulty_progression: Whether problems should increase in difficulty
            
        Returns:
            List of problem dictionaries
        """
        logger.info(f"Generating {count} practice problems for: {topic}")
        
        prompt = PRACTICE_PROBLEM_TEMPLATE.format(
            topic=topic,
            level=level,
            count=count,
            progressive=difficulty_progression
        )
        
        content = await self.generate_content(prompt, temperature=0.8, max_tokens=2000)
        
        # Parse the response into structured problems
        problems = self._parse_practice_problems(content, count)
        return problems
    
    def _parse_practice_problems(self, content: str, expected_count: int) -> List[Dict[str, Any]]:
        """Parse LLM-generated practice problems into structured format"""
        problems = []
        lines = content.split('\n')
        
        current_problem = {}
        for line in lines:
            line = line.strip()
            if line.startswith('Problem'):
                if current_problem:
                    problems.append(current_problem)
                current_problem = {'text': line.split(':', 1)[1].strip() if ':' in line else line}
            elif line.startswith('Hint:'):
                current_problem['hint'] = line.split(':', 1)[1].strip()
            elif line.startswith('Difficulty:'):
                current_problem['difficulty'] = line.split(':', 1)[1].strip().lower()
        
        if current_problem:
            problems.append(current_problem)
        
        # Fill in any missing problems with basic structure
        while len(problems) < expected_count:
            problems.append({
                'text': f"Practice problem {len(problems) + 1}",
                'hint': "Think about the key concepts from the lesson",
                'difficulty': 'medium'
            })
        
        return problems[:expected_count]
    
    async def assess_student_response(
        self,
        topic: str,
        question: str,
        student_answer: str,
        correct_answer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assess a student's response and provide feedback
        
        Args:
            topic: The topic being assessed
            question: The original question
            student_answer: Student's response
            correct_answer: The correct answer (if available)
            
        Returns:
            Assessment dictionary with feedback
        """
        logger.info(f"Assessing student response for topic: {topic}")
        
        prompt = ASSESSMENT_TEMPLATE.format(
            topic=topic,
            question=question,
            student_answer=student_answer,
            correct_answer=correct_answer or "Not provided - assess understanding qualitatively"
        )
        
        content = await self.generate_content(prompt, temperature=0.6, max_tokens=1000)
        
        return {
            'topic': topic,
            'question': question,
            'student_answer': student_answer,
            'assessment_feedback': content,
            'timestamp': datetime.now().isoformat()
        }
    
    async def explain_math_concept(
        self,
        topic: str,
        level: str,
        question: str = "Explain this concept"
    ) -> str:
        """Generate math-specific explanation"""
        prompt = MATH_TUTOR_TEMPLATE.format(
            topic=topic,
            level=level,
            question=question
        )
        return await self.generate_content(prompt, temperature=0.5, max_tokens=1500)
    
    async def explain_science_concept(
        self,
        topic: str,
        subject: str,
        level: str,
        question: str = "Explain this concept"
    ) -> str:
        """Generate science-specific explanation"""
        prompt = SCIENCE_TUTOR_TEMPLATE.format(
            topic=topic,
            subject=subject,
            level=level,
            question=question
        )
        return await self.generate_content(prompt, temperature=0.6, max_tokens=1500)
    
    async def explain_programming_concept(
        self,
        language: str,
        concept: str,
        level: str,
        question: str = "Explain this concept"
    ) -> str:
        """Generate programming-specific explanation"""
        prompt = PROGRAMMING_TUTOR_TEMPLATE.format(
            language=language,
            concept=concept,
            level=level,
            question=question
        )
        return await self.generate_content(prompt, temperature=0.4, max_tokens=2000)


def create_llm_manager(
    use_openai: bool = None,
    use_ollama: bool = None
) -> EducationalLLMManager:
    """
    Factory function to create LLM manager with env vars
    
    Args:
        use_openai: Override env var for OpenAI usage
        use_ollama: Override env var for Ollama usage
        
    Returns:
        EducationalLLMManager instance
    """
    if use_openai is None:
        use_openai = os.getenv('USE_OPENAI', 'true').lower() == 'true'
    
    if use_ollama is None:
        use_ollama = os.getenv('USE_OLLAMA', 'true').lower() == 'true'
    
    return EducationalLLMManager(
        use_openai=use_openai,
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        openai_model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
        use_ollama=use_ollama,
        ollama_host=os.getenv('OLLAMA_HOST', 'http://localhost:11434'),
        ollama_model=os.getenv('OLLAMA_MODEL', 'llama2')
    )
