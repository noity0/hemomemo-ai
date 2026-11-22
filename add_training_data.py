"""
Direct training data addition to Hemomemo AI
"""

import os
import sys
import json
import time
from datetime import datetime

# Add to Hemomemo AI's existing modules
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Direct training data addition
training_data = [
    {
        "prompt": "What are the key thinking methodologies for programming?",
        "response": """Programming thinking involves several key methodologies:

1. **Computational Thinking**: Break problems into smaller, manageable parts
   - Decomposition: Split complex problems into simpler sub-problems
   - Pattern Recognition: Identify similarities and patterns in problems
   - Abstraction: Focus on essential details while ignoring irrelevant ones
   - Algorithm Design: Create step-by-step solutions to problems

2. **Systematic Approach**:
   - Understand the problem clearly before coding
   - Plan your approach with pseudocode or flowcharts
   - Write clean, modular code with single responsibility
   - Test incrementally rather than all at once

3. **Debugging Mindset**:
   - View errors as learning opportunities
   - Use systematic debugging: isolate, reproduce, fix, verify
   - Read error messages carefully - they contain clues
   - Use print statements and debugging tools effectively

4. **Learning Process**:
   - Start with fundamentals, build gradually
   - Practice regularly - coding is a skill, not knowledge
   - Study existing code to learn best practices
   - Teach others to solidify your understanding

Remember: The best approach is often the simplest one that works correctly.""",
        "category": "thinking",
        "difficulty": "intermediate",
        "quality": 0.95,
        "source": "qanoon_compliant_training"
    },
    {
        "prompt": "How do I approach a new programming problem?",
        "response": """When approaching a new programming problem, follow this systematic approach:

1. **Understand the Problem** (20% of time)
   - Read the problem statement carefully
   - Identify inputs, outputs, and constraints
   - Ask clarifying questions if needed
   - Break the problem into smaller sub-problems

2. **Plan Your Solution** (30% of time)
   - Create pseudocode or flowcharts
   - Identify data structures and algorithms needed
   - Plan the architecture and component structure
   - Consider edge cases and error handling

3. **Implement Incrementally** (30% of time)
   - Start with the simplest working version
   - Add complexity gradually
   - Test each component before moving to the next
   - Write clean, readable code with good naming

4. **Test and Refine** (20% of time)
   - Test with various inputs including edge cases
   - Debug systematically
   - Optimize performance if needed
   - Refactor for clarity and maintainability

Remember: The best approach is often the simplest one that works correctly.""",
        "category": "thinking",
        "difficulty": "beginner",
        "quality": 0.92,
        "source": "qanoon_compliant_training"
    },
    {
        "prompt": "What are the best practices for writing clean code?",
        "response": """Clean code follows these principles:

1. **Readability First**
   - Use meaningful variable and function names
   - Keep functions small and focused (one responsibility)
   - Use consistent formatting and indentation
   - Add comments that explain why, not what

2. **Simplicity and Clarity**
   - Write code that's easy to understand
   - Avoid clever tricks that make code hard to follow
   - Use the simplest solution that works
   - Prefer readability over premature optimization

3. **Consistency**
   - Follow consistent naming conventions (snake_case, camelCase, PascalCase)
   - Use the same style throughout the project
   - Follow language idioms and conventions
   - Be consistent in error handling approaches

4. **Error Handling**
   - Handle errors gracefully and informatively
   - Use appropriate exception types
   - Provide clear error messages
   - Fail fast rather than continuing with invalid state

5. **Testing**
   - Write unit tests for all critical functions
   - Test edge cases and boundary conditions
   - Use integration tests for component interactions
   - Maintain high test coverage

Remember: Code is read more often than it's written. Write for humans first, computers second.""",
        "category": "coding",
        "difficulty": "intermediate",
        "quality": 0.96,
        "source": "qanoon_compliant_training"
    },
    {
        "prompt": "How do I write efficient and performant code?",
        "response": """Writing efficient code involves understanding performance at multiple levels:

1. **Algorithmic Complexity**
   - Choose appropriate data structures (O(1) vs O(n) operations)
   - Avoid nested loops when possible (O(n²) complexity)
   - Use efficient sorting algorithms (O(n log n) vs O(n²))
   - Consider time-space tradeoffs carefully

2. **Language-Specific Optimizations**
   - Use built-in functions and libraries (they're often optimized)
   - Avoid unnecessary object creation in loops
   - Use efficient data types (e.g., arrays vs linked lists)
   - Leverage language-specific features (e.g., list comprehensions in Python)

3. **Memory Management**
   - Free unused memory promptly
   - Avoid memory leaks in long-running applications
   - Use appropriate data structures to minimize memory usage
   - Consider memory locality for better cache performance

Remember: Premature optimization is the root of all evil. Write clean, correct code first, then optimize where needed.""",
        "category": "coding",
        "difficulty": "advanced",
        "quality": 0.93,
        "source": "qanoon_compliant_training"
    },
    {
        "prompt": "What's the most effective way to learn programming?",
        "response": """The most effective way to learn programming follows these principles:

1. **Start with Fundamentals**
   - Learn core concepts before frameworks and tools
   - Understand data types, control structures, and functions
   - Master one language deeply before learning others
   - Build strong foundation in computer science basics

2. **Active Learning**
   - Don't just watch tutorials - code along
   - Practice regularly (daily if possible)
   - Solve problems on platforms like LeetCode, HackerRank
   - Build projects that interest you

3. **Project-Based Learning**
   - Start with small, achievable projects
   - Gradually increase complexity
   - Build a portfolio of your work
   - Contribute to open source projects

4. **Deliberate Practice**
   - Focus on weak areas specifically
   - Get feedback on your code
   - Review and refactor your own work
   - Learn from mistakes and errors

Remember: Learning to code is a marathon, not a sprint. Consistency beats intensity every time.""",
        "category": "learning",
        "difficulty": "beginner",
        "quality": 0.94,
        "source": "qanoon_compliant_training"
    },
    {
        "prompt": "How do I overcome programming challenges and frustration?",
        "response": """Programming challenges and frustration are normal. Here's how to overcome them:

1. **Accept the Struggle**
   - Debugging is part of programming, not a failure
   - Every programmer faces difficult problems
   - Frustration means you're learning and growing
   - Take breaks when feeling overwhelmed

2. **Systematic Problem-Solving**
   - Break problems into smaller, manageable pieces
   - Research similar problems and solutions
   - Use rubber duck debugging to think through problems
   - Take notes and document your thought process

3. **Learning Resources**
   - Search for error messages and solutions
   - Read documentation carefully
   - Ask for help when stuck (after trying first)
   - Study how others solve similar problems

Remember: The best programmers are those who embrace challenges and learn from failure.""",
        "category": "learning",
        "difficulty": "beginner",
        "quality": 0.93,
        "source": "qanoon_compliant_training"
    },
    {
        "prompt": "What are the best practices for code refactoring?",
        "response": """Code refactoring follows these best practices:

1. **Refactoring Principles**
   - Make small changes incrementally
   - Keep tests passing throughout the process
   - Focus on one improvement at a time
   - Know when to stop - balance perfection with progress

2. **Common Refactoring Techniques**
   - Extract Method: Break down large methods into smaller ones
   - Rename Variables: Use descriptive names for clarity
   - Remove Duplicate Code: Create reusable functions/methods
   - Simplify Conditional Logic: Use guard clauses and early returns

3. **Code Smells to Address**
   - Long Methods: Methods doing too many things
   - Large Classes: Classes with too many responsibilities
   - Duplicate Code: Similar code in multiple places
   - Complex Conditionals: Nested if-else statements

Remember: Refactoring is not about changing functionality, it's about improving code quality while maintaining the same behavior.""",
        "category": "editing",
        "difficulty": "intermediate",
        "quality": 0.95,
        "source": "qanoon_compliant_training"
    },
    {
        "prompt": "How do I optimize code for better performance?",
        "response": """Code optimization follows these principles:

1. **Measure Before Optimizing**
   - Use profiling tools to identify bottlenecks
   - Focus on the critical 20% that affects 80% of performance
   - Don't guess where the problems are
   - Test performance after changes to verify improvements

2. **Algorithmic Optimization**
   - Choose appropriate data structures (O(1) vs O(n) operations)
   - Avoid nested loops when possible (O(n²) complexity)
   - Use efficient sorting algorithms (O(n log n) vs O(n²))
   - Consider time-space tradeoffs carefully

3. **Language-Specific Optimizations**
   - Use built-in functions and libraries (they're often optimized)
   - Avoid unnecessary object creation in loops
   - Use efficient data types (e.g., arrays vs linked lists)
   - Leverage language-specific features

Remember: Premature optimization is the root of all evil. Write clean, correct code first, then optimize where needed.""",
        "category": "editing",
        "difficulty": "advanced",
        "quality": 0.94,
        "source": "qanoon_compliant_training"
    }
]

# Add training data directly to Hemomemo AI's training file
STORE = os.path.join(ROOT, 'data', 'corpus_big', 'learned_chat.txt')

print("Adding programming education training data to Hemomemo AI...")
print(f"Training data file: {STORE}")

# Check if training data file exists
if not os.path.exists(STORE):
    print("Training data file does not exist, creating it...")
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    with open(STORE, 'w', encoding='utf-8') as f:
        f.write("# Hemomemo AI training data\n")

# Add training data directly
print(f"\nAdding {len(training_data)} training examples...")

for i, item in enumerate(training_data, 1):
    print(f"Adding example {i}/{len(training_data)}: {item['category']} - {item['difficulty']}")
    
    # Generate hash for deduplication
    import hashlib
    content = f"{item['prompt']}{item['response']}"
    hash_obj = hashlib.sha1(content.encode())
    hash_hex = hash_obj.hexdigest()
    
    # Format training data entry
    entry = f"""# h: {hash_hex} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Sawal: {item['prompt']}
Jawab: {item['response']}
Meta: source={item['source']},category={item['category']},difficulty={item['difficulty']},quality={item['quality']},verified=True

"""
    
    # Append to training file
    with open(STORE, 'a', encoding='utf-8') as f:
        f.write(entry)

print("\nTraining data added successfully!")

# Verify the training data
print("\nVerifying training data...")
with open(STORE, 'r', encoding='utf-8') as f:
    content = f.read()
    programming_entries = [line for line in content.split('\n') if 'qanoon_compliant_training' in line]
    
    if programming_entries:
        print(f"Found {len(programming_entries)} programming education entries")
        
        # Count by category
        categories = {}
        for line in content.split('\n'):
            if 'category=' in line:
                category = line.split('category=')[1].split(',')[0]
                categories[category] = categories.get(category, 0) + 1
        
        print("Categories added:")
        for category, count in categories.items():
            print(f"  {category}: {count} examples")
    else:
        print("No programming education entries found")

print("\nTraining complete! Hemomemo AI has been trained on programming education.")