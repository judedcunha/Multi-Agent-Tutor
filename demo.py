"""
Phase 2 Demo Script
Demonstrates LLM Integration, Specialized Agents, and Advanced RAG
"""

import sys
import os
from pathlib import Path
import asyncio
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_subsection(title):
    """Print a formatted subsection"""
    print(f"\n--- {title} ---\n")


def validate_practice_problems(problems: List[Dict], topic: str) -> Dict[str, Any]:
    """
    Comprehensive validation for practice problems 
    
    Returns:
        Dict with 'valid', 'issues', and 'details' keys
    """
    issues = []
    details = {
        'total': len(problems),
        'valid': 0,
        'invalid': 0,
        'missing_fields': []
    }
    
    for i, problem in enumerate(problems, 1):
        problem_issues = []
        
        # Check for text field
        if not problem.get('text'):
            problem_issues.append(f"Problem {i}: Missing 'text' field")
        elif len(problem['text'].strip()) < 10:
            problem_issues.append(f"Problem {i}: Text too short ({len(problem['text'])} chars)")
        elif problem['text'].startswith('[') or 'placeholder' in problem['text'].lower():
            problem_issues.append(f"Problem {i}: Text appears to be a placeholder")
        
        # Check for hint
        if not problem.get('hint'):
            problem_issues.append(f"Problem {i}: Missing 'hint' field")
        
        # Check for difficulty
        if not problem.get('difficulty'):
            problem_issues.append(f"Problem {i}: Missing 'difficulty' field")
        elif problem['difficulty'] not in ['easy', 'medium', 'hard']:
            problem_issues.append(f"Problem {i}: Invalid difficulty '{problem['difficulty']}'")
        
        if problem_issues:
            issues.extend(problem_issues)
            details['invalid'] += 1
            details['missing_fields'].append(i)
        else:
            details['valid'] += 1
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'details': details
    }


async def demo_llm_manager():
    """Demonstrate LLM Manager capabilities"""
    print_section("1. EDUCATIONAL LLM MANAGER DEMO")
    
    try:
        from llm.educational_clients import create_llm_manager
        
        print("Initializing LLM Manager...")
        llm = create_llm_manager()
        
        if not llm.use_openai and not llm.use_ollama:
            print("WARNING: No LLM service available")
            print("   To enable: Set OPENAI_API_KEY in .env or install/run Ollama")
            print("   Skipping LLM demos...\n")
            return False
        
        print(f"PASS: LLM Manager initialized")
        print(f"   OpenAI: {'Active' if llm.use_openai else 'Inactive'}")
        print(f"   Ollama: {'Active' if llm.use_ollama else 'Inactive'}")
        
        # Demo 1: Lesson Explanation
        print_subsection("Demo 1: Generate Lesson Explanation")
        print("Topic: Python list comprehensions")
        print("Level: Beginner")
        print("Learning Style: Visual\n")
        
        try:
            explanation = await llm.create_lesson_explanation(
                topic="Python list comprehensions",
                level="beginner",
                learning_style="visual",
                student_context={'prior_knowledge': ['Python basics', 'loops']}
            )
            
            print("Generated Explanation:")
            print("-" * 70)
            # Show first 500 chars
            print(explanation[:500] + "..." if len(explanation) > 500 else explanation)
            print("-" * 70)
            print(f"PASS: Generated {len(explanation)} characters of educational content")
        except Exception as e:
            print(f"FAIL: Failed to generate explanation: {e}")
        
        # Demo 2: Practice Problems
        print_subsection("Demo 2: Generate Practice Problems")
        print("Topic: Basic algebra")
        print("Level: Beginner")
        print("Count: 3 problems\n")
        
        try:
            problems = await llm.generate_practice_problems(
                topic="Basic algebra equations",
                level="beginner",
                count=3,
                difficulty_progression=True
            )
            
            print("Generated Practice Problems:")
            print("-" * 70)
            for i, problem in enumerate(problems, 1):
                print(f"\nProblem {i}:")
                text = problem.get('text', 'N/A')
                print(f"  Text: {text[:150]}..." if len(text) > 150 else f"  Text: {text}")
                if 'hint' in problem:
                    hint = problem['hint']
                    print(f"  Hint: {hint[:100]}..." if len(hint) > 100 else f"  Hint: {hint}")
                if 'difficulty' in problem:
                    print(f"  Difficulty: {problem['difficulty']}")
            print("-" * 70)
            
            # Validate quality 
            validation = validate_practice_problems(problems, "Basic algebra")
            if validation['valid']:
                print(f"PASS: Generated {validation['details']['valid']}/{validation['details']['total']} complete practice problems")
            else:
                print(f"FAIL: Quality issues found:")
                for issue in validation['issues']:
                    print(f"    - {issue}")
                print(f"  Valid: {validation['details']['valid']}/{validation['details']['total']}")
        except Exception as e:
            print(f"FAIL: Failed to generate problems: {e}")
        
        return True
        
    except ImportError as e:
        print(f"FAIL: LLM Manager not available: {e}")
        print("   Install with: pip install openai ollama")
        return False


async def demo_specialized_agents():
    """Demonstrate Specialized Subject Agents"""
    print_section("2. SPECIALIZED SUBJECT AGENTS DEMO")
    
    try:
        from agents.subject_experts import create_specialized_agents
        from llm.educational_clients import create_llm_manager
        
        # Create LLM manager (can be None)
        try:
            llm = create_llm_manager()
        except:
            llm = None
            print("WARNING: LLM not available - agents will use fallback mode\n")
        
        agents = create_specialized_agents(llm)
        
        print("PASS: Specialized Agents Created:")
        print(f"   Math Tutor")
        print(f"   Science Tutor")
        print(f"   Programming Tutor\n")
        
        # Demo 1: Math Tutor
        print_subsection("Demo 1: Math Tutor Agent")
        math_tutor = agents['math_tutor']
        
        print("Explaining: Quadratic equations")
        print("Level: Intermediate\n")
        
        explanation = await math_tutor.explain_math_concept(
            concept="Quadratic equations",
            level="intermediate",
            include_examples=True
        )
        
        print("Math Tutor Response:")
        print("-" * 70)
        print(f"Concept: {explanation['concept']}")
        print(f"Level: {explanation['level']}")
        main_exp = explanation['main_explanation']
        print(f"Explanation: {main_exp[:300]}..." if len(main_exp) > 300 else main_exp)
        if 'examples' in explanation:
            print(f"\nExamples provided: {len(explanation['examples'])}")
        if 'visualization_suggestions' in explanation:
            print(f"Visualizations suggested: {len(explanation['visualization_suggestions'])}")
        print("-" * 70)
        print("PASS: Math explanation complete\n")
        
        # Demo 2: Science Tutor
        print_subsection("Demo 2: Science Tutor Agent")
        science_tutor = agents['science_tutor']
        
        print("Explaining: Photosynthesis")
        print("Subject: Biology")
        print("Level: Beginner\n")
        
        explanation = await science_tutor.explain_scientific_concept(
            concept="Photosynthesis",
            subject="biology",
            level="beginner"
        )
        
        print("Science Tutor Response:")
        print("-" * 70)
        print(f"Concept: {explanation['concept']}")
        print(f"Subject: {explanation['subject']}")
        main_exp = explanation['main_explanation']
        print(f"Explanation: {main_exp[:300]}..." if len(main_exp) > 300 else main_exp)
        if 'real_world_applications' in explanation:
            print(f"\nReal-world applications: {len(explanation['real_world_applications'])}")
        print("-" * 70)
        print("PASS: Science explanation complete\n")
        
        # Demo 3: Programming Tutor
        print_subsection("Demo 3: Programming Tutor Agent")
        prog_tutor = agents['programming_tutor']
        
        print("Explaining: Python functions")
        print("Language: Python")
        print("Level: Beginner\n")
        
        explanation = await prog_tutor.explain_code_concept(
            language="Python",
            concept="functions",
            level="beginner"
        )
        
        print("Programming Tutor Response:")
        print("-" * 70)
        print(f"Language: {explanation['language']}")
        print(f"Concept: {explanation['concept']}")
        main_exp = explanation['main_explanation']
        print(f"Explanation: {main_exp[:300]}..." if len(main_exp) > 300 else main_exp)
        if 'code_examples' in explanation:
            print(f"\nCode examples: {len(explanation['code_examples'])}")
        if 'best_practices' in explanation:
            print(f"Best practices: {len(explanation['best_practices'])}")
        print("-" * 70)
        print("PASS: Programming explanation complete\n")
        
        return True
        
    except ImportError as e:
        print(f"FAIL: Specialized Agents not available: {e}")
        return False


async def demo_advanced_rag():
    """Demonstrate Advanced RAG System"""
    print_section("3. ADVANCED RAG SYSTEM DEMO")
    
    try:
        from rag.educational_retrieval import create_rag_system
        
        print("Initializing RAG System...")
        rag, reranker = create_rag_system()
        
        if not rag.initialized:
            print("WARNING: RAG system not fully initialized")
            print("   Install dependencies: pip install chromadb sentence-transformers")
            print("   Skipping RAG demos...\n")
            return False
        
        print("PASS: RAG System initialized")
        print(f"   Vector DB: ChromaDB")
        print(f"   Embedder: Sentence Transformers")
        print(f"   Reranker: Cross-Encoder\n")
        
        # Demo 1: Index Content
        print_subsection("Demo 1: Index Educational Content")
        
        sample_content = [
            {
                'id': 'py_lists_1',
                'text': 'Python lists are ordered, mutable collections that can store items of different types. They are defined using square brackets.',
                'metadata': {'subject': 'programming', 'level': 'beginner', 'topic': 'python lists'}
            },
            {
                'id': 'py_loops_1',
                'text': 'For loops in Python allow you to iterate over sequences like lists, tuples, and strings. They use the syntax: for item in sequence.',
                'metadata': {'subject': 'programming', 'level': 'beginner', 'topic': 'python loops'}
            },
            {
                'id': 'py_functions_1',
                'text': 'Functions in Python are defined using the def keyword and allow code reuse. They can accept parameters and return values.',
                'metadata': {'subject': 'programming', 'level': 'beginner', 'topic': 'python functions'}
            },
            {
                'id': 'math_algebra_1',
                'text': 'Algebra involves solving equations with unknown variables. Basic algebra uses operations like addition, subtraction, multiplication, and division.',
                'metadata': {'subject': 'math', 'level': 'beginner', 'topic': 'algebra'}
            }
        ]
        
        print(f"Indexing {len(sample_content)} educational resources...")
        success = await rag.index_educational_content(sample_content)
        
        if success:
            print(f"PASS: Successfully indexed {len(sample_content)} documents\n")
        else:
            print("FAIL: Failed to index content\n")
            return False
        
        # Demo 2: Semantic Search
        print_subsection("Demo 2: Semantic Search")
        
        query = "How do I work with lists in Python?"
        print(f"Query: '{query}'")
        print(f"Searching for top 3 results...\n")
        
        results = await rag.retrieve_educational_content(
            query=query,
            subject="programming",
            student_level="beginner",
            top_k=3
        )
        
        print("Search Results:")
        print("-" * 70)
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"  Content: {result['content'][:100]}...")
            print(f"  Score: {result['score']:.3f}")
            print(f"  Relevance: {result['relevance']}")
        print("-" * 70)
        print(f"PASS: Retrieved {len(results)} relevant documents\n")
        
        # Demo 3: Hybrid Search
        print_subsection("Demo 3: Hybrid Search (Semantic + Keyword)")
        
        query = "Python iteration"
        print(f"Query: '{query}'")
        print(f"Using hybrid search...\n")
        
        results = await rag.hybrid_search(
            query=query,
            subject="programming",
            student_level="beginner",
            top_k=2
        )
        
        print("Hybrid Search Results:")
        print("-" * 70)
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"  Content: {result['content'][:100]}...")
            print(f"  Combined Score: {result.get('combined_score', 0):.3f}")
        print("-" * 70)
        print(f"PASS: Hybrid search complete\n")
        
        # Demo 4: Re-ranking
        print_subsection("Demo 4: Cross-Encoder Re-ranking")
        
        if reranker.initialized and results:
            print("Re-ranking results for better relevance...")
            
            reranked = reranker.rerank_for_learning(
                candidates=results,
                query=query,
                student_level="beginner"
            )
            
            print("\nRe-ranked Results:")
            print("-" * 70)
            for i, result in enumerate(reranked, 1):
                print(f"\nResult {i}:")
                print(f"  Content: {result['content'][:100]}...")
                if 'rerank_score' in result:
                    print(f"  Rerank Score: {result['rerank_score']:.3f}")
            print("-" * 70)
            print("PASS: Re-ranking complete\n")
        else:
            print("WARNING: Re-ranker not available or no results to rerank\n")
        
        return True
        
    except ImportError as e:
        print(f"FAIL: RAG System not available: {e}")
        print("   Install with: pip install chromadb sentence-transformers")
        return False


async def demo_integrated_system():
    """Demonstrate fully integrated Phase 2 system"""
    print_section("4. INTEGRATED MULTI-AGENT SYSTEM (Phase 1 + Phase 2)")
    
    try:
        from agents.tutoring_graph import AdvancedTutoringSystem
        from agents.state_schema import StudentProfile
        
        print("Initializing Advanced Tutoring System with Phase 2 features...")
        
        system = AdvancedTutoringSystem(
            enable_llm=True,
            enable_specialized_agents=True,
            enable_advanced_rag=True
        )
        
        print("PASS: System initialized\n")
        
        # Show system status
        status = system.get_system_status()
        
        print("System Status:")
        print("-" * 70)
        print(f"Version: {status['version']}")
        print(f"Phase: {status['phase']}")
        print(f"Active Agents: {status['agents']['count']}")
        print(f"\nPhase 2 Features:")
        print(f"  LLM Integration: {status['features']['llm_integration']}")
        if status['features']['llm_integration']:
            print(f"  LLM Provider: {status['features']['llm_provider']}")
            if status.get('llm_details'):
                llm_details = status['llm_details']
                if llm_details['openai']['enabled']:
                    print(f"    - OpenAI: PASS ({llm_details['openai']['model']})")
                else:
                    print(f"    - OpenAI: FAIL")
                if llm_details['ollama']['enabled']:
                    print(f"    - Ollama: PASS ({llm_details['ollama']['model']})")
                else:
                    print(f"    - Ollama: FAIL")
        print(f"  Specialized Agents: {status['features']['specialized_agents']}")
        if status['features']['specialized_agents']:
            specialized = status['agents']['specialized']
            print(f"    - Math Tutor: {'PASS' if specialized['math_tutor'] else 'FAIL'}")
            print(f"    - Science Tutor: {'PASS' if specialized['science_tutor'] else 'FAIL'}")
            print(f"    - Programming Tutor: {'PASS' if specialized['programming_tutor'] else 'FAIL'}")
        print(f"  Advanced RAG: {status['features']['advanced_rag']}")
        if status['features']['advanced_rag'] and status.get('rag_details'):
            rag = status['rag_details']
            print(f"    - Vector DB: {rag.get('vector_db', 'N/A')}")
            print(f"    - Embedder: {rag.get('embedder', 'N/A')}")
            print(f"    - Reranker: {rag.get('reranker', 'N/A')}")
        print("-" * 70)
        
        # Test teaching session
        print_subsection("Teaching Session Demo")
        
        student = StudentProfile(
            name="Demo Student",
            level="beginner",
            learning_style="visual",
            learning_goals=["Learn Python programming"]
        )
        
        print(f"Student: {student.name}")
        print(f"Level: {student.level}")
        print(f"Learning Style: {student.learning_style}")
        print(f"Topic: Python list comprehensions\n")
        
        print("Running multi-agent teaching session...")
        print("(This may take a moment if using LLM features)\n")
        
        session = system.teach_topic("Python list comprehensions", student)
        
        print("Session Results:")
        print("-" * 70)
        print(f"PASS: Session completed successfully")
        print(f"\nSubject: {session['detected_subject']}")
        print(f"Level: {session['teaching_level']}")
        print(f"Agents Involved: {session['agent_count']}")
        print(f"Agent Chain: {' → '.join(session['agents_involved'][:4])}...")
        print(f"\nLesson Objectives: {len(session['lesson_plan'].get('objectives', []))}")
        print(f"Educational Resources: {len(session['educational_content'])}")
        print(f"Practice Problems: {len(session['practice_problems'])}")
        
        if 'explanation' in session and 'generated_by' in session['explanation']:
            print(f"\nContent Generation: {session['explanation']['generated_by'].upper()}")
        
        print(f"\nSession Status: {session['learning_progress'].get('completion_status', 'unknown')}")
        print(f"Errors: {len(session['errors'])}")
        print("-" * 70)
        
        return True
        
    except Exception as e:
        print(f"FAIL: System demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Phase 2 demos"""
    print("\n" + "=" * 70)
    print("  PHASE 2 DEMONSTRATION: LLM, Specialized Agents, and Advanced RAG")
    print("=" * 70)
    print("\nThis demo showcases the new Phase 2 features:")
    print("  1. Educational LLM Manager (OpenAI/Ollama)")
    print("  2. Specialized Subject Agents (Math/Science/Programming)")
    print("  3. Advanced RAG System (ChromaDB + Semantic Search)")
    print("  4. Integrated Multi-Agent System")
    print("\nNote: Some features require API keys or additional setup.")
    print("See docs/PHASE2_COMPLETE.md for configuration details.\n")
    
    input("Press Enter to begin demos...")
    
    # Run demos
    results = []
    
    results.append(await demo_llm_manager())
    results.append(await demo_specialized_agents())
    results.append(await demo_advanced_rag())
    results.append(await demo_integrated_system())
    
    # Final summary
    print_section("DEMO SUMMARY")
    
    demos = [
        "LLM Manager",
        "Specialized Agents",
        "Advanced RAG",
        "Integrated System"
    ]
    
    print("Demo Results:")
    print("-" * 70)
    for demo, result in zip(demos, results):
        status = "PASS" if result else "SKIPPED/FAILED"
        print(f"{status}  {demo}")
    print("-" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n{passed}/{total} demos completed successfully")
    
    if passed == total:
        print("\nSUCCESS: All Phase 2 features are working!")
    elif passed > 0:
        print("\nPARTIAL: Some Phase 2 features are working")
        print("   Check configuration for features that were skipped")
    else:
        print("\nWARNING: Phase 2 features not available")
        print("   Install dependencies: pip install -r requirements.txt")
        print("   Configure API keys in .env file")
    
    print("\nFor more information:")
    print("   - docs/PHASE2_COMPLETE.md (Full documentation)")
    print("   - verify_phase2.py (Check installation)")
    print("   - .env (Configuration file)")
    print()


if __name__ == "__main__":
    asyncio.run(main())