"""
Specialized Subject Agents - Phase 2 Implementation
Domain-specific educational agents for Math, Science, and Programming
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MathTutorAgent:
    """
    Specialized agent for mathematics education
    Handles mathematical concepts, problem-solving, and visualizations
    """
    
    def __init__(self, llm_manager=None):
        """
        Initialize Math Tutor Agent
        
        Args:
            llm_manager: EducationalLLMManager instance for content generation
        """
        self.llm = llm_manager
        self.sympy_available = False
        
        # Try to import SymPy for symbolic math
        try:
            import sympy
            self.sympy = sympy
            self.sympy_available = True
            logger.info("Math Tutor Agent initialized with SymPy support")
        except ImportError:
            logger.warning("SymPy not available - symbolic math features limited")
            self.sympy = None
        
        logger.info("Math Tutor Agent initialized")
    
    async def explain_math_concept(
        self,
        concept: str,
        level: str = "beginner",
        include_examples: bool = True
    ) -> Dict[str, Any]:
        """
        Explain a mathematical concept with examples
        
        Args:
            concept: The math concept to explain
            level: Student level
            include_examples: Whether to include worked examples
            
        Returns:
            Dictionary with explanation and examples
        """
        logger.info(f"Explaining math concept: {concept} (level: {level})")
        
        explanation = {
            'concept': concept,
            'level': level,
            'timestamp': datetime.now().isoformat()
        }
        
        # Use LLM if available
        if self.llm:
            try:
                explanation['main_explanation'] = await self.llm.explain_math_concept(
                    topic=concept,
                    level=level
                )
                logger.info("Generated LLM-based math explanation")
            except Exception as e:
                logger.error(f"LLM explanation failed: {e}")
                explanation['main_explanation'] = self._generate_basic_explanation(concept, level)
        else:
            explanation['main_explanation'] = self._generate_basic_explanation(concept, level)
        
        # Add examples if requested
        if include_examples:
            explanation['examples'] = self._generate_math_examples(concept, level)
        
        # Add visualization suggestions
        explanation['visualization_suggestions'] = self._suggest_visualizations(concept)
        
        return explanation
    
    def _generate_basic_explanation(self, concept: str, level: str) -> str:
        """Generate basic rule-based math explanation"""
        explanations = {
            'algebra': f"Algebra ({level} level) involves working with variables and equations to solve for unknown values.",
            'geometry': f"Geometry ({level} level) is the study of shapes, sizes, and spatial relationships.",
            'calculus': f"Calculus ({level} level) deals with rates of change and accumulation.",
            'statistics': f"Statistics ({level} level) involves collecting, analyzing, and interpreting data."
        }
        
        for key, value in explanations.items():
            if key in concept.lower():
                return value
        
        return f"Mathematical concept: {concept} at {level} level. This involves understanding the fundamental principles and applying them to solve problems."
    
    def _generate_math_examples(self, concept: str, level: str) -> List[Dict[str, str]]:
        """Generate example problems"""
        # Basic examples - in production, these would be more sophisticated
        examples = []
        
        if 'algebra' in concept.lower():
            if level == 'beginner':
                examples.append({
                    'problem': 'Solve for x: 2x + 5 = 13',
                    'solution_steps': '1. Subtract 5 from both sides: 2x = 8\n2. Divide by 2: x = 4',
                    'answer': 'x = 4'
                })
            else:
                examples.append({
                    'problem': 'Solve for x: x² - 5x + 6 = 0',
                    'solution_steps': '1. Factor: (x-2)(x-3) = 0\n2. Set each factor to 0\n3. x = 2 or x = 3',
                    'answer': 'x = 2 or x = 3'
                })
        
        if not examples:
            examples.append({
                'problem': f'Example problem for {concept}',
                'solution_steps': 'Step-by-step solution would go here',
                'answer': 'Final answer'
            })
        
        return examples
    
    def _suggest_visualizations(self, concept: str) -> List[str]:
        """Suggest visualizations for the concept"""
        suggestions = []
        
        if 'graph' in concept.lower() or 'function' in concept.lower():
            suggestions.append("Plot the function on a coordinate plane")
            suggestions.append("Show key points (intercepts, maxima, minima)")
        
        if 'geometry' in concept.lower():
            suggestions.append("Draw labeled diagrams of shapes")
            suggestions.append("Show angle measurements and side lengths")
        
        if 'calculus' in concept.lower():
            suggestions.append("Visualize derivatives as slopes")
            suggestions.append("Show area under curves for integrals")
        
        if not suggestions:
            suggestions.append("Use diagrams to illustrate the concept")
            suggestions.append("Create step-by-step visual guides")
        
        return suggestions
    
    async def solve_math_problem(
        self,
        problem: str,
        show_steps: bool = True
    ) -> Dict[str, Any]:
        """
        Solve a math problem with detailed steps
        
        Args:
            problem: The problem to solve
            show_steps: Whether to show step-by-step solution
            
        Returns:
            Dictionary with solution
        """
        logger.info(f"Solving math problem: {problem}")
        
        solution = {
            'problem': problem,
            'timestamp': datetime.now().isoformat()
        }
        
        # Try SymPy if available
        if self.sympy_available:
            try:
                solution['symbolic_solution'] = self._sympy_solve(problem)
            except Exception as e:
                logger.warning(f"SymPy solving failed: {e}")
        
        # Use LLM for explanation
        if self.llm:
            try:
                explanation = await self.llm.generate_content(
                    f"Solve this math problem step-by-step:\n{problem}\n\nShow all work clearly.",
                    temperature=0.3,
                    max_tokens=1000
                )
                solution['solution_explanation'] = explanation
            except Exception as e:
                logger.error(f"LLM solution failed: {e}")
                solution['solution_explanation'] = "Unable to generate detailed solution at this time."
        else:
            solution['solution_explanation'] = "LLM not available for detailed solutions."
        
        return solution
    
    def _sympy_solve(self, problem: str) -> str:
        """Use SymPy to solve mathematical expressions"""
        # This is a simplified implementation
        # In production, would parse the problem more intelligently
        try:
            from sympy import sympify, solve, symbols
            x = symbols('x')
            # This would need more sophisticated parsing
            return "SymPy solution available with proper parsing"
        except:
            return "Unable to parse with SymPy"


class ScienceTutorAgent:
    """
    Specialized agent for science education
    Handles physics, chemistry, biology concepts
    """
    
    def __init__(self, llm_manager=None):
        """Initialize Science Tutor Agent"""
        self.llm = llm_manager
        logger.info("Science Tutor Agent initialized")
    
    async def explain_scientific_concept(
        self,
        concept: str,
        subject: str,
        level: str = "beginner"
    ) -> Dict[str, Any]:
        """
        Explain a scientific concept
        
        Args:
            concept: The science concept
            subject: The science subject (physics/chemistry/biology)
            level: Student level
            
        Returns:
            Dictionary with explanation
        """
        logger.info(f"Explaining {subject} concept: {concept} (level: {level})")
        
        explanation = {
            'concept': concept,
            'subject': subject,
            'level': level,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.llm:
            try:
                explanation['main_explanation'] = await self.llm.explain_science_concept(
                    topic=concept,
                    subject=subject,
                    level=level
                )
            except Exception as e:
                logger.error(f"LLM explanation failed: {e}")
                explanation['main_explanation'] = self._generate_basic_science_explanation(concept, subject, level)
        else:
            explanation['main_explanation'] = self._generate_basic_science_explanation(concept, subject, level)
        
        # Add real-world applications
        explanation['real_world_applications'] = self._find_real_world_applications(concept, subject)
        
        # Add experiment suggestions
        explanation['experiment_suggestions'] = self._suggest_experiments(concept, subject, level)
        
        return explanation
    
    def _generate_basic_science_explanation(self, concept: str, subject: str, level: str) -> str:
        """Generate basic science explanation"""
        return f"{subject.capitalize()} concept: {concept}\n\nThis {level}-level concept explores fundamental principles in {subject}. Understanding this concept helps explain natural phenomena and scientific processes."
    
    def _find_real_world_applications(self, concept: str, subject: str) -> List[str]:
        """Find real-world applications of the concept"""
        applications = []
        
        if subject == 'physics':
            applications.append("Engineering and technology design")
            applications.append("Understanding natural phenomena")
        elif subject == 'chemistry':
            applications.append("Medicine and pharmaceutical development")
            applications.append("Materials science and manufacturing")
        elif subject == 'biology':
            applications.append("Healthcare and medicine")
            applications.append("Environmental conservation")
        
        return applications
    
    def _suggest_experiments(self, concept: str, subject: str, level: str) -> List[Dict[str, str]]:
        """Suggest safe experiments"""
        experiments = []
        
        if level == 'beginner':
            experiments.append({
                'name': f'Simple {concept} demonstration',
                'description': 'Safe, hands-on activity to explore the concept',
                'safety_note': 'Adult supervision recommended'
            })
        
        return experiments


class ProgrammingTutorAgent:
    """
    Specialized agent for programming education
    Handles code concepts, examples, and debugging
    """
    
    def __init__(self, llm_manager=None):
        """Initialize Programming Tutor Agent"""
        self.llm = llm_manager
        logger.info("Programming Tutor Agent initialized")
    
    async def explain_code_concept(
        self,
        language: str,
        concept: str,
        level: str = "beginner"
    ) -> Dict[str, Any]:
        """
        Explain a programming concept
        
        Args:
            language: Programming language
            concept: The programming concept
            level: Student level
            
        Returns:
            Dictionary with explanation and examples
        """
        logger.info(f"Explaining {language} concept: {concept} (level: {level})")
        
        explanation = {
            'language': language,
            'concept': concept,
            'level': level,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.llm:
            try:
                explanation['main_explanation'] = await self.llm.explain_programming_concept(
                    language=language,
                    concept=concept,
                    level=level
                )
            except Exception as e:
                logger.error(f"LLM explanation failed: {e}")
                explanation['main_explanation'] = self._generate_basic_code_explanation(language, concept, level)
        else:
            explanation['main_explanation'] = self._generate_basic_code_explanation(language, concept, level)
        
        # Add code examples
        explanation['code_examples'] = await self._generate_code_examples(language, concept, level)
        
        # Add common pitfalls
        explanation['common_pitfalls'] = self._list_common_pitfalls(language, concept)
        
        # Add best practices
        explanation['best_practices'] = self._list_best_practices(language, concept)
        
        return explanation
    
    def _generate_basic_code_explanation(self, language: str, concept: str, level: str) -> str:
        """Generate basic programming explanation"""
        return f"{language} programming concept: {concept}\n\nThis {level}-level concept is fundamental to writing effective {language} code. Understanding this concept will help you write cleaner, more efficient programs."
    
    async def _generate_code_examples(
        self,
        language: str,
        concept: str,
        level: str
    ) -> List[Dict[str, str]]:
        """Generate code examples"""
        examples = []
        
        # Basic template - LLM would generate better examples
        if language.lower() == 'python':
            examples.append({
                'title': f'Basic {concept} example',
                'code': f'# {concept} in Python\n# Example code would go here',
                'explanation': f'This demonstrates {concept} in Python'
            })
        
        return examples
    
    def _list_common_pitfalls(self, language: str, concept: str) -> List[str]:
        """List common programming pitfalls"""
        return [
            f"Common mistake when using {concept} in {language}",
            "Watch out for edge cases",
            "Remember proper syntax and indentation"
        ]
    
    def _list_best_practices(self, language: str, concept: str) -> List[str]:
        """List best practices"""
        return [
            "Write clear, readable code with good variable names",
            "Add comments to explain complex logic",
            "Test your code with different inputs",
            "Follow language-specific style guidelines"
        ]
    
    async def debug_student_code(
        self,
        code: str,
        error_message: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Help debug student code
        
        Args:
            code: The student's code
            error_message: The error they're encountering
            language: Programming language
            
        Returns:
            Dictionary with debugging help
        """
        logger.info(f"Debugging {language} code with error: {error_message}")
        
        debug_help = {
            'language': language,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.llm:
            try:
                prompt = f"""Help debug this {language} code:

```{language}
{code}
```

Error message: {error_message}

Provide:
1. Explanation of what's causing the error
2. Suggested fix
3. Tips to avoid this error in the future
"""
                debug_help['debugging_help'] = await self.llm.generate_content(
                    prompt,
                    temperature=0.3,
                    max_tokens=1000
                )
            except Exception as e:
                logger.error(f"LLM debugging help failed: {e}")
                debug_help['debugging_help'] = f"Error encountered: {error_message}\n\nReview the code carefully and check for syntax errors."
        else:
            debug_help['debugging_help'] = f"Error: {error_message}\n\nCheck your code syntax and logic carefully."
        
        return debug_help


def create_specialized_agents(llm_manager=None) -> Dict[str, Any]:
    """
    Factory function to create all specialized agents
    
    Args:
        llm_manager: EducationalLLMManager instance
        
    Returns:
        Dictionary of specialized agents
    """
    return {
        'math_tutor': MathTutorAgent(llm_manager),
        'science_tutor': ScienceTutorAgent(llm_manager),
        'programming_tutor': ProgrammingTutorAgent(llm_manager)
    }
