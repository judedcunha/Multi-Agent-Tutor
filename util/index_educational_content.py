"""
Index Educational Content into Vector Database
Populates ChromaDB with educational materials for RAG retrieval
"""

import sys
import os
import asyncio
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

print("📚 Educational Content Indexing System")
print("=" * 70)

# Educational content organized by subject
EDUCATIONAL_CONTENT = {
    "programming": {
        "python_basics": [
            {
                "title": "Python Variables and Data Types",
                "content": """
Python variables are containers for storing data values. Unlike other programming languages, 
Python has no command for declaring a variable - you create one the moment you assign a value to it.

Basic data types include:
- Integers (int): Whole numbers like 5, -3, 1000
- Floats (float): Decimal numbers like 3.14, -0.5, 2.0
- Strings (str): Text in quotes like "hello", 'world'
- Booleans (bool): True or False values

Example:
age = 25          # integer
price = 19.99     # float
name = "Alice"    # string
is_student = True # boolean

Python is dynamically typed, meaning variables can change type after creation.
                """,
                "level": "beginner",
                "topic": "python variables"
            },
            {
                "title": "Python Lists and Arrays",
                "content": """
Lists are ordered, mutable collections in Python. They can contain items of different types 
and are defined using square brackets [].

Key operations:
- Creating: my_list = [1, 2, 3, 4, 5]
- Accessing: my_list[0] returns first element
- Slicing: my_list[1:3] returns elements from index 1 to 2
- Appending: my_list.append(6) adds to end
- Removing: my_list.remove(3) removes value 3
- Length: len(my_list) returns number of items

Lists are zero-indexed, meaning counting starts at 0. Negative indices count from the end.
Example: my_list[-1] gets the last element.

Common methods: append(), extend(), insert(), remove(), pop(), clear(), sort(), reverse()
                """,
                "level": "beginner",
                "topic": "python lists"
            },
            {
                "title": "Python Functions and Parameters",
                "content": """
Functions are reusable blocks of code that perform specific tasks. They help organize code 
and avoid repetition.

Defining functions:
def greet(name):
    return f"Hello, {name}!"

Key concepts:
- def keyword: Starts function definition
- Parameters: Variables in parentheses that receive values
- Return statement: Sends a value back to caller
- Docstrings: Documentation strings in triple quotes

Types of parameters:
- Positional: def add(a, b)
- Default: def greet(name="World")
- Keyword: def info(name="", age=0)
- Variable-length: def sum_all(*numbers)

Functions promote code reuse, make testing easier, and improve readability.
                """,
                "level": "beginner",
                "topic": "python functions"
            },
            {
                "title": "Python Loops - For and While",
                "content": """
Loops allow you to execute code repeatedly. Python has two main types: for and while loops.

For Loops:
Used when you know how many times to iterate.
for i in range(5):
    print(i)  # Prints 0, 1, 2, 3, 4

for item in my_list:
    print(item)  # Iterates through each item

While Loops:
Used when you don't know how many iterations needed.
count = 0
while count < 5:
    print(count)
    count += 1

Loop control:
- break: Exits loop immediately
- continue: Skips to next iteration
- else: Executes if loop completes normally (not broken)

Common use cases: Processing collections, counting, searching, generating sequences.
                """,
                "level": "beginner",
                "topic": "python loops"
            },
            {
                "title": "Python Dictionaries and Key-Value Pairs",
                "content": """
Dictionaries store data as key-value pairs. They're unordered, mutable, and indexed by keys 
instead of positions.

Creating dictionaries:
student = {
    "name": "Alice",
    "age": 20,
    "grade": "A"
}

Operations:
- Access: student["name"] returns "Alice"
- Add/Update: student["email"] = "alice@email.com"
- Remove: del student["age"]
- Check key: "name" in student returns True
- Get keys: student.keys()
- Get values: student.values()
- Get items: student.items()

Methods: get(), pop(), update(), clear(), copy()

Dictionaries are extremely fast for lookups and perfect for storing related data with 
meaningful labels instead of numeric indices.
                """,
                "level": "beginner",
                "topic": "python dictionaries"
            },
            {
                "title": "Python Classes and Object-Oriented Programming",
                "content": """
Classes are blueprints for creating objects. They bundle data (attributes) and 
functionality (methods) together.

Basic class structure:
class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def introduce(self):
        return f"I'm {self.name}, {self.age} years old"

Key concepts:
- __init__: Constructor method, runs when object created
- self: References the instance itself
- Attributes: Variables belonging to the object
- Methods: Functions belonging to the object
- Instantiation: student1 = Student("Alice", 20)

Benefits of OOP:
- Encapsulation: Group related data and functions
- Reusability: Create multiple objects from one class
- Organization: Structure code logically
- Inheritance: Build on existing classes

OOP makes complex programs more manageable and maintainable.
                """,
                "level": "intermediate",
                "topic": "python oop"
            }
        ],
        "python_advanced": [
            {
                "title": "Python List Comprehensions",
                "content": """
List comprehensions provide a concise way to create lists based on existing lists or other iterables.

Basic syntax:
new_list = [expression for item in iterable if condition]

Examples:
- Squares: [x**2 for x in range(10)]
- Filtering: [x for x in numbers if x > 0]
- Transform: [s.upper() for s in strings]
- Nested: [[i*j for j in range(3)] for i in range(3)]

Advantages:
- More readable than traditional loops
- Often faster execution
- More Pythonic code style
- Can replace map() and filter()

List comprehensions can include conditions and nested iterations, making them powerful 
tools for data transformation.
                """,
                "level": "intermediate",
                "topic": "python comprehensions"
            },
            {
                "title": "Python Decorators",
                "content": """
Decorators modify or enhance functions without changing their source code. They wrap 
another function to extend its behavior.

Basic decorator:
def my_decorator(func):
    def wrapper():
        print("Before function")
        func()
        print("After function")
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

Common uses:
- Logging function calls
- Timing execution
- Access control/authentication
- Caching results
- Input validation

Decorators with arguments:
def repeat(times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(times):
                func(*args, **kwargs)
        return wrapper
    return decorator

Decorators are a powerful metaprogramming tool in Python.
                """,
                "level": "advanced",
                "topic": "python decorators"
            }
        ]
    },
    
    "mathematics": {
        "algebra": [
            {
                "title": "Understanding Algebraic Equations",
                "content": """
Algebraic equations express relationships between variables and constants. Solving equations 
means finding the value(s) of variables that make the equation true.

Basic concepts:
- Variable: Unknown value represented by letters (x, y, z)
- Coefficient: Number multiplying a variable (3x has coefficient 3)
- Constant: Fixed number in equation
- Equality: Both sides must have same value

Simple equations:
2x + 5 = 13
Steps to solve:
1. Subtract 5 from both sides: 2x = 8
2. Divide both sides by 2: x = 4

Key principle: Whatever you do to one side, do to the other to maintain equality.

Practice maintaining balance and performing inverse operations to isolate variables.
                """,
                "level": "beginner",
                "topic": "algebra equations"
            },
            {
                "title": "Linear Equations and Graphing",
                "content": """
Linear equations create straight lines when graphed. They follow the form y = mx + b.

Components:
- m = slope (rate of change, rise over run)
- b = y-intercept (where line crosses y-axis)
- x = independent variable
- y = dependent variable

Slope calculation:
m = (y₂ - y₁) / (x₂ - x₁)

Example: y = 2x + 3
- Slope is 2 (goes up 2 for every 1 right)
- Y-intercept is 3 (crosses y-axis at 3)

Graphing steps:
1. Plot y-intercept (0, b)
2. Use slope to find another point
3. Draw line through points

Linear equations model many real-world relationships: speed, cost, growth, etc.
                """,
                "level": "intermediate",
                "topic": "linear equations"
            }
        ],
        "calculus": [
            {
                "title": "Introduction to Derivatives",
                "content": """
Derivatives measure how a function changes as its input changes. They represent the 
instantaneous rate of change or slope of a function at any point.

Concept:
The derivative of f(x) at x=a is the slope of the tangent line at that point.

Notation:
- f'(x) or dy/dx or df/dx

Basic rules:
- Power rule: d/dx(x^n) = nx^(n-1)
- Constant rule: d/dx(c) = 0
- Sum rule: d/dx(f + g) = f' + g'

Examples:
- f(x) = x² → f'(x) = 2x
- f(x) = x³ → f'(x) = 3x²
- f(x) = 5x → f'(x) = 5

Applications: Optimization, velocity, acceleration, marginal cost in economics.

Derivatives are fundamental to understanding change in mathematics and science.
                """,
                "level": "advanced",
                "topic": "calculus derivatives"
            }
        ]
    },
    
    "science": {
        "physics": [
            {
                "title": "Newton's Laws of Motion",
                "content": """
Newton's three laws describe how objects move and interact with forces.

First Law (Inertia):
An object at rest stays at rest, an object in motion stays in motion, unless acted 
upon by an external force. Objects resist changes in their state of motion.

Second Law (F = ma):
Force equals mass times acceleration. The acceleration of an object depends on the 
net force acting on it and its mass.

Third Law (Action-Reaction):
For every action, there is an equal and opposite reaction. Forces always come in pairs.

Real-world examples:
- Seatbelts (First Law): Stop your body when car stops
- Pushing cart (Second Law): Heavier cart needs more force
- Rocket propulsion (Third Law): Exhaust pushes down, rocket pushes up

These laws form the foundation of classical mechanics and engineering.
                """,
                "level": "beginner",
                "topic": "physics motion"
            },
            {
                "title": "Energy and Conservation",
                "content": """
Energy is the capacity to do work. It exists in many forms and can transform between 
them, but the total amount in a closed system remains constant.

Types of energy:
- Kinetic: Energy of motion (KE = ½mv²)
- Potential: Stored energy (gravitational: PE = mgh)
- Thermal: Heat energy from particle motion
- Chemical: Stored in bonds between atoms
- Electrical: Flow of charged particles

Law of Conservation of Energy:
Energy cannot be created or destroyed, only transformed from one form to another.

Example: Roller coaster
- Top of hill: Maximum PE, minimal KE
- Bottom: Maximum KE, minimal PE
- Total energy constant (ignoring friction)

Understanding energy transformations is key to physics, chemistry, and engineering.
                """,
                "level": "intermediate",
                "topic": "physics energy"
            }
        ],
        "chemistry": [
            {
                "title": "Atoms and Elements",
                "content": """
Atoms are the basic building blocks of matter. Everything around you is made of atoms.

Structure of an atom:
- Nucleus: Center, contains protons (+) and neutrons (neutral)
- Electrons: Orbit nucleus in shells, negatively charged (-)
- Protons determine element identity
- Electrons determine chemical behavior

Elements:
Pure substances made of only one type of atom. 118 elements known, organized in 
the periodic table.

Important concepts:
- Atomic number: Number of protons
- Mass number: Protons + neutrons
- Isotopes: Same element, different neutrons
- Ions: Atoms with gained/lost electrons

Example: Carbon
- Atomic number: 6 (6 protons)
- Common isotope: Carbon-12 (6 protons + 6 neutrons)
- Forms basis of organic chemistry and life

Understanding atoms is fundamental to all of chemistry and materials science.
                """,
                "level": "beginner",
                "topic": "chemistry atoms"
            }
        ]
    },
    
    "general": {
        "study_skills": [
            {
                "title": "Effective Note-Taking Strategies",
                "content": """
Good notes help you remember information, understand concepts, and prepare for exams.

Cornell Method:
- Divide page into 3 sections: Notes, Cues, Summary
- Take notes during class in main area
- Add keywords/questions in cues section
- Summarize key points at bottom

Mind Mapping:
- Central concept in middle
- Branch out with related ideas
- Use colors and images
- Shows connections between concepts

Tips for better notes:
1. Don't write everything - focus on main ideas
2. Use your own words to aid understanding
3. Leave space for additions later
4. Review within 24 hours to reinforce memory
5. Use abbreviations consistently
6. Highlight or underline key terms

Active note-taking engages your brain and improves retention significantly.
                """,
                "level": "beginner",
                "topic": "study skills"
            },
            {
                "title": "Time Management for Students",
                "content": """
Effective time management reduces stress and improves academic performance.

Priority Matrix (Eisenhower Box):
- Urgent & Important: Do first (deadlines, emergencies)
- Important, Not Urgent: Schedule (studying, planning)
- Urgent, Not Important: Delegate or minimize
- Neither: Eliminate

Planning techniques:
1. Use a calendar or planner
2. Break large tasks into smaller steps
3. Set specific, achievable goals
4. Time block for focused work
5. Build in buffer time for unexpected issues

Study schedule tips:
- Study during your peak energy times
- Take 5-10 minute breaks every hour
- Review material regularly, not just before exams
- Start assignments when assigned, not when due
- Schedule recreation time too

The Pomodoro Technique: 25 minutes focused work, 5 minute break, repeat.

Good time management creates balance between academics, activities, and personal time.
                """,
                "level": "beginner",
                "topic": "time management"
            }
        ]
    }
}


async def index_content():
    """Index all educational content into ChromaDB"""
    
    print("\n🔧 STEP 1: Initializing RAG System")
    print("-" * 70)
    
    try:
        from rag.educational_retrieval import EducationalRAG
        
        # RAG initializes in __init__, no separate initialize() method
        rag = EducationalRAG()
        print("✅ RAG system initialized")
        
    except Exception as e:
        print(f"❌ Failed to initialize RAG: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n📖 STEP 2: Preparing Educational Content")
    print("-" * 70)
    
    documents = []
    doc_count = 0
    
    for subject, categories in EDUCATIONAL_CONTENT.items():
        for category, items in categories.items():
            for item in items:
                doc_id = f"{subject}_{category}_{doc_count}"
                
                document = {
                    'id': doc_id,
                    'text': f"{item['title']}\n\n{item['content'].strip()}",
                    'metadata': {
                        'subject': subject,
                        'category': category,
                        'topic': item['topic'],
                        'level': item['level'],
                        'title': item['title'],
                        'source': 'curated_educational_content',
                        'indexed_at': datetime.now().isoformat()
                    }
                }
                
                documents.append(document)
                doc_count += 1
                print(f"  Prepared: {item['title']} ({subject}/{item['level']})")
    
    print(f"\n📚 Total documents prepared: {len(documents)}")
    
    print("\n💾 STEP 3: Indexing into ChromaDB")
    print("-" * 70)
    
    try:
        await rag.index_educational_content(documents)
        print(f"✅ Successfully indexed {len(documents)} documents!")
        
    except Exception as e:
        print(f"❌ Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n🔍 STEP 4: Verifying Indexed Content")
    print("-" * 70)
    
    try:
        # Test search for each subject
        test_queries = [
            ("Python variables", "programming", "beginner"),
            ("functions in Python", "programming", "beginner"),
            ("algebra equations", "mathematics", "beginner"),
            ("Newton's laws", "science", "beginner"),
            ("study tips", "general", "beginner")
        ]
        
        for query, subject, level in test_queries:
            results = await rag.hybrid_search(
                query=query,
                subject=subject,
                student_level=level,
                top_k=3
            )
            
            print(f"\nQuery: '{query}' ({subject}/{level})")
            print(f"  Results found: {len(results)}")
            
            if results:
                for i, result in enumerate(results[:2], 1):
                    title = result['metadata'].get('title', 'No title')
                    score = result.get('combined_score', 0)
                    print(f"  {i}. {title} (score: {score:.3f})")
            else:
                print("  ⚠️ No results found")
        
        print("\n✅ Verification complete!")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n📊 STEP 5: Checking Search Statistics")
    print("-" * 70)
    
    try:
        stats = rag.get_search_statistics()
        print(f"Collection name: {stats.get('collection_name')}")
        print(f"Total documents: {stats.get('total_documents', 0)}")
        print(f"BM25 available: {stats.get('bm25_available', False)}")
        print(f"Semantic search ready: {stats.get('semantic_search_ready', False)}")
        print(f"Hybrid search ready: {stats.get('hybrid_search_available', False)}")
        
    except Exception as e:
        print(f"Error getting stats: {e}")
    
    print("\n" + "=" * 70)
    print("📚 INDEXING COMPLETE")
    print("=" * 70)
    
    print(f"\n✅ Indexed {len(documents)} educational documents")
    print(f"✅ Subjects: {list(EDUCATIONAL_CONTENT.keys())}")
    print(f"✅ Topics: Python, Math, Physics, Chemistry, Study Skills")
    print(f"✅ Levels: Beginner, Intermediate, Advanced")
    
    print("\n🎓 Content Summary:")
    for subject, categories in EDUCATIONAL_CONTENT.items():
        count = sum(len(items) for items in categories.values())
        print(f"  - {subject.capitalize()}: {count} documents")
    
    print("\n🚀 Next Steps:")
    print("  1. Restart your server: python src/main_tutor.py")
    print("  2. Make a teaching request")
    print("  3. RAG will now retrieve relevant resources!")
    print("  4. Check logs for 'Retrieved X resources via Advanced RAG'")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\nStarting educational content indexing...")
    print("This will populate the vector database with curated educational materials.\n")
    
    try:
        asyncio.run(index_content())
        print("\n✅ SUCCESS! Educational content indexed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Indexing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
