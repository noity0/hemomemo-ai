"""
🎓 enhanced_programming_education.py — INTEGRATED PROGRAMMING EDUCATION SYSTEM
==========================================================================
Enhances Hemomemo AI's existing prompt understanding system with programming education capabilities.
Integrates with the flow engine to provide comprehensive programming education support.

QANOON: 100% local, no external AI platforms, no FFmpeg, no cloud dependencies.
"""

import os
import sys
import json
import time
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Add to Hemomemo AI's existing modules
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from model.prompt_understanding import PromptUnderstandingSystem
from model.flow_engine import ARCHETYPES, STAGE_LABEL
from model.learner import learn_from_chat, _TRUSTED

class ProgrammingEducationSystem:
    """
    Enhanced programming education system integrated with Hemomemo AI's existing capabilities.
    Adds programming-specific flow archetypes and educational prompt handling.
    """
    
    def __init__(self):
        self.prompt_system = PromptUnderstandingSystem()
        self.programming_categories = {
            'thinking': 'Programming thinking methodologies and problem-solving',
            'coding': 'Best practices and techniques for writing quality code',
            'learning': 'How to learn programming effectively and efficiently',
            'editing': 'Code optimization, refactoring, and improvement strategies',
            'debugging': 'Debugging techniques and error resolution',
            'algorithms': 'Algorithm design and implementation',
            'data_structures': 'Data structure selection and usage',
            'design_patterns': 'Software design patterns and their applications'
        }
        
        # Programming-specific flow archetypes
        self.programming_archetypes = {
            'programming_thinking': ('READ', 'UNDERSTAND', 'THINK', 'REASON', 'ANSWER'),
            'coding_practice': ('READ', 'UNDERSTAND', 'TOKEN_BREAK', 'CODE', 'VERIFY', 'ANSWER'),
            'learning_strategy': ('READ', 'UNDERSTAND', 'RETRIEVE', 'LEARN', 'APPLY', 'ANSWER'),
            'code_editing': ('READ', 'UNDERSTAND', 'ANALYZE', 'REFACTOR', 'OPTIMIZE', 'ANSWER'),
            'debugging': ('READ', 'UNDERSTAND', 'IDENTIFY', 'DEBUG', 'VERIFY', 'ANSWER'),
            'algorithms': ('READ', 'UNDERSTAND', 'DESIGN', 'IMPLEMENT', 'TEST', 'OPTIMIZE', 'ANSWER'),
            'data_structures': ('READ', 'UNDERSTAND', 'SELECT', 'IMPLEMENT', 'ANALYZE', 'OPTIMIZE', 'ANSWER'),
            'design_patterns': ('READ', 'UNDERSTAND', 'APPLY', 'IMPLEMENT', 'VERIFY', 'ANSWER')
        }
        
        # Educational prompts and responses
        self.educational_content = self._load_educational_content()
        
        # Initialize with Hemomemo AI's existing archetypes
        self._integrate_with_existing_archetypes()
    
    def _load_educational_content(self):
        """Load programming education content from training data"""
        content = {}
        
        # Try to load from training reports
        training_dirs = [
            'data/training_reports',
            'data/corpus_big'
        ]
        
        for training_dir in training_dirs:
            if os.path.exists(training_dir):
                for filename in os.listdir(training_dir):
                    if filename.endswith('.json') or filename.endswith('.txt'):
                        filepath = os.path.join(training_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                if filename.endswith('.json'):
                                    data = json.load(f)
                                    # Extract programming education content
                                    if isinstance(data, dict):
                                        if 'programming_education' in str(data):
                                            content.update(self._extract_programming_content(data))
                                else:
                                    # Process text files
                                    lines = f.readlines()
                                    content.update(self._extract_content_from_text(lines))
                        except Exception as e:
                            print(f"Warning: Could not load {filepath}: {e}")
        
        return content
    
    def _extract_programming_content(self, data):
        """Extract programming education content from JSON data"""
        content = {}
        
        def extract_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if 'programming' in key.lower() or 'education' in key.lower() or 'training' in key.lower():
                        if isinstance(value, (str, list)):
                            content[current_path] = value
                    elif isinstance(value, (dict, list)):
                        extract_recursive(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_recursive(item, f"{path}[{i}]")
        
        extract_recursive(data)
        return content
    
    def _extract_content_from_text(self, lines):
        """Extract programming content from text files"""
        content = {}
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('# ') and 'programming' in line.lower():
                current_section = line[2:]
                content[current_section] = []
            elif current_section and line and not line.startswith('#'):
                content[current_section].append(line)
        
        # Convert lists to strings
        return {k: '\n'.join(v) for k, v in content.items() if v}
    
    def _integrate_with_existing_archetypes(self):
        """Integrate programming archetypes with Hemomemo AI's existing flow engine"""
        # Add programming archetypes to existing ones
        ARCHETYPES.update(self.programming_archetypes)
        
        # Update stage labels for programming
        programming_stages = {
            'CODE': 'code likh raha hoon',
            'LEARN': 'seekh raha hoon',
            'ANALYZE': 'analyze kar raha hoon',
            'REFACTOR': 'refactor kar raha hoon',
            'OPTIMIZE': 'optimize kar raha hoon',
            'IDENTIFY': 'identify kar raha hoon',
            'DESIGN': 'design kar raha hoon',
            'SELECT': 'select kar raha hoon',
            'APPLY': 'apply kar raha hoon',
            'TEST': 'test kar raha hoon'
        }
        
        STAGE_LABEL.update(programming_stages)
    
    def detect_programming_intent(self, prompt: str) -> Dict:
        """
        Detect if the user is asking about programming education and categorize the request.
        """
        prompt_lower = prompt.lower()
        
        # Programming education keywords
        programming_keywords = {
            'thinking': ['think', 'approach', 'methodology', 'strategy', 'how to think', 'problem solving'],
            'coding': ['code', 'programming', 'development', 'best practice', 'clean code', 'pattern'],
            'learning': ['learn', 'study', 'education', 'tutorial', 'how to learn', 'beginner', 'advanced'],
            'editing': ['edit', 'refactor', 'optimize', 'improve', 'fix', 'rewrite', 'clean up'],
            'debugging': ['debug', 'error', 'bug', 'fix', 'issue', 'problem', 'exception'],
            'algorithms': ['algorithm', 'data structure', 'sort', 'search', 'traverse', 'optimize'],
            'design_patterns': ['pattern', 'design pattern', 'architecture', 'structure', 'mvc', 'singleton'],
            'general': ['programming', 'code', 'developer', 'software', 'computer', 'tech']
        }
        
        # Detect intent
        detected_categories = {}
        scores = {}
        
        for category, keywords in programming_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in prompt_lower:
                    score += 1
            
            if score > 0:
                detected_categories[category] = score
                scores[category] = score
        
        # Return the best match
        if detected_categories:
            best_category = max(scores, key=scores.get)
            confidence = scores[best_category] / max(len(programming_keywords[best_category]), 1)
            
            return {
                'is_programming_education': True,
                'category': best_category,
                'confidence': confidence,
                'all_categories': detected_categories,
                'archetype': self.programming_archetypes.get(f'{best_category}_thinking', self.programming_archetypes['programming_thinking'])
            }
        else:
            return {
                'is_programming_education': False,
                'category': None,
                'confidence': 0.0,
                'all_categories': {},
                'archetype': None
            }
    
    def generate_educational_response(self, prompt: str, category: str) -> str:
        """
        Generate a comprehensive educational response based on the detected category.
        """
        # Get educational content for the category
        category_content = self.educational_content.get(category, {})
        
        # Generate educational response based on category
        if category == 'thinking':
            return self._generate_thinking_response(prompt)
        elif category == 'coding':
            return self._generate_coding_response(prompt)
        elif category == 'learning':
            return self._generate_learning_response(prompt)
        elif category == 'editing':
            return self._generate_editing_response(prompt)
        elif category == 'debugging':
            return self._generate_debugging_response(prompt)
        elif category == 'algorithms':
            return self._generate_algorithms_response(prompt)
        elif category == 'data_structures':
            return self._generate_data_structures_response(prompt)
        elif category == 'design_patterns':
            return self._generate_design_patterns_response(prompt)
        else:
            return self._generate_general_programming_response(prompt)
    
    def _generate_thinking_response(self, prompt: str) -> str:
        """Generate programming thinking methodology response"""
        return f"""🧠 Programming Thinking Methodology

When approaching programming problems, follow this systematic thinking process:

1. **Understand the Problem**
   - Read the problem statement carefully
   - Identify inputs, outputs, and constraints
   - Ask clarifying questions if needed
   - Break the problem into smaller sub-problems

2. **Plan Your Approach**
   - Create pseudocode or flowcharts
   - Identify data structures and algorithms needed
   - Plan the architecture and component structure
   - Consider edge cases and error handling

3. **Implement Incrementally**
   - Start with the simplest working version
   - Add complexity gradually
   - Test each component before moving to the next
   - Write clean, readable code with good naming

4. **Test and Refine**
   - Test with various inputs including edge cases
   - Debug systematically
   - Optimize performance if needed
   - Refactor for clarity and maintainability

Key thinking patterns:
- **Divide and Conquer**: Break large problems into smaller pieces
- **Pattern Recognition**: Identify common problem types and solutions
- **Abstraction**: Focus on essential details, ignore irrelevant ones
- **Algorithmic Thinking**: Design step-by-step solutions

Remember: The best code is often the simplest code that works correctly."""
    
    def _generate_coding_response(self, prompt: str) -> str:
        """Generate coding best practices response"""
        return f"""💻 Coding Best Practices

Write clean, maintainable code with these principles:

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

3. **Error Handling**
   - Handle errors gracefully and informatively
   - Use appropriate exception types
   - Provide clear error messages
   - Fail fast rather than continuing with invalid state

4. **Testing**
   - Write unit tests for all critical functions
   - Test edge cases and boundary conditions
   - Use integration tests for component interactions
   - Maintain high test coverage

5. **Design Patterns**
   - Use appropriate design patterns for your problem
   - Don't over-engineer - use patterns when they add value
   - Understand the tradeoffs of each pattern
   - Document pattern usage in your code

Essential patterns to know:
- **Singleton**: Single instance of a class
- **Factory**: Create objects without specifying exact classes
- **Observer**: Notify multiple objects of state changes
- **Strategy**: Define family of algorithms, make them interchangeable

Remember: Code is read more often than it's written. Write for humans first, computers second."""
    
    def _generate_learning_response(self, prompt: str) -> str:
        """Generate programming learning strategy response"""
        return f"""📚 Effective Programming Learning Strategies

Learn programming effectively with these strategies:

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

5. **Community and Collaboration**
   - Join coding communities and forums
   - Pair program with other developers
   - Attend meetups and conferences
   - Find mentors and ask questions

Learning resources:
- **Books**: For deep understanding and theory
- **Interactive platforms**: For hands-on practice
- **Documentation**: For reference and details
- **Video tutorials**: For visual learners

Remember: Learning to code is a marathon, not a sprint. Consistency beats intensity every time."""
    
    def _generate_editing_response(self, prompt: str) -> str:
        """Generate code editing and refactoring response"""
        return f"""✏️ Code Editing and Refactoring Techniques

Improve your code with these editing and refactoring strategies:

1. **Refactoring Principles**
   - Make small changes incrementally
   - Keep tests passing throughout the process
   - Focus on one improvement at a time
   - Know when to stop - balance perfection with progress

2. **Common Refactoring Techniques**
   - **Extract Method**: Break down large methods into smaller ones
   - **Rename Variables**: Use descriptive names for clarity
   - **Remove Duplicate Code**: Create reusable functions/methods
   - **Simplify Conditional Logic**: Use guard clauses and early returns

3. **Code Smells to Address**
   - **Long Methods**: Methods doing too many things
   - **Large Classes**: Classes with too many responsibilities
   - **Duplicate Code**: Similar code in multiple places
   - **Complex Conditionals**: Nested if-else statements

4. **Performance Optimization**
   - Profile before optimizing (don't guess)
   - Focus on the critical 20% that affects 80% of performance
   - Use efficient data structures and algorithms
   - Consider time-space tradeoffs

5. **Code Quality Improvements**
   - Improve readability and maintainability
   - Reduce complexity and improve testability
   - Enhance documentation and comments
   - Follow consistent coding standards

Remember: Refactoring is not about changing functionality, it's about improving code quality while maintaining the same behavior."""
    
    def _generate_debugging_response(self, prompt: str) -> str:
        """Generate debugging techniques response"""
        return f"""🐛 Debugging Techniques and Strategies

Debug effectively with these systematic approaches:

1. **Debugging Mindset**
   - View errors as learning opportunities
   - Be systematic and patient
   - Read error messages carefully - they contain clues
   - Use debugging tools and techniques

2. **Systematic Debugging Process**
   - **Reproduce**: Create a minimal test case that shows the bug
   - **Isolate**: Narrow down the code causing the issue
   - **Hypothesize**: Form a hypothesis about the cause
   - **Test**: Verify your hypothesis by modifying the code
   - **Fix**: Implement the solution
   - **Verify**: Ensure the fix works and doesn't introduce new bugs

3. **Debugging Tools and Techniques**
   - Print statements and logging
   - Debuggers and breakpoints
   - Unit tests for edge cases
   - Rubber duck debugging (explain to an inanimate object)

4. **Common Debugging Scenarios**
   - **Null Reference**: Check for uninitialized variables
   - **Off-by-One Errors**: Verify array/index bounds
   - **Logic Errors**: Review conditional statements
   - **Resource Leaks**: Ensure proper cleanup

5. **Prevention Strategies**
   - Write defensive code with proper error handling
   - Use assertions for invariants
   - Write comprehensive tests
   - Code review and pair programming

Remember: Every programmer debugs. The best programmers are the best debuggers."""
    
    def _generate_algorithms_response(self, prompt: str) -> str:
        """Generate algorithm design response"""
        return f"""🔍 Algorithm Design and Implementation

Design effective algorithms with these principles:

1. **Algorithm Design Process**
   - Understand the problem requirements
   - Choose appropriate data structures
   - Design step-by-step solution
   - Analyze time and space complexity
   - Implement and test thoroughly

2. **Common Algorithm Patterns**
   - **Sorting**: QuickSort, MergeSort, HeapSort
   - **Searching**: Binary Search, Depth-First Search, Breadth-First Search
   - **Dynamic Programming**: Break into overlapping subproblems
   - **Greedy Algorithms**: Make locally optimal choices
   - **Divide and Conquer**: Solve smaller instances of the same problem

3. **Complexity Analysis**
   - **Time Complexity**: O(1), O(log n), O(n), O(n log n), O(n²)
   - **Space Complexity**: Memory usage analysis
   - **Tradeoffs**: Balance between time and space
   - **Big O Notation**: Formal complexity analysis

4. **Implementation Best Practices**
   - Write clear, readable code
   - Handle edge cases and errors
   - Add comments explaining the algorithm
   - Test with various inputs and sizes

5. **Optimization Techniques**
   - Choose appropriate data structures
   - Avoid unnecessary computations
   - Use memoization for repeated calculations
   - Consider parallel processing for large datasets

Remember: The best algorithm is often the simplest one that solves the problem correctly."""
    
    def _generate_data_structures_response(self, prompt: str) -> str:
        """Generate data structure selection response"""
        return f"""📊 Data Structure Selection and Usage

Choose the right data structures for your needs:

1. **Common Data Structures**
   - **Arrays**: Fixed-size, O(1) access, O(n) insertion/deletion
   - **Linked Lists**: Dynamic size, O(n) access, O(1) insertion/deletion
   - **Stacks**: LIFO (Last In, First Out), O(1) push/pop
   - **Queues**: FIFO (First In, First Out), O(1) enqueue/dequeue
   - **Hash Tables**: O(1) average case for insert, delete, search
   - **Trees**: Hierarchical data, various types (binary, BST, AVL, etc.)
   - **Graphs**: Network relationships, nodes and edges

2. **Selection Criteria**
   - **Access Pattern**: How often do you need to access elements?
   - **Insertion/Deletion**: How often do elements change?
   - **Memory Usage**: How much memory is available?
   - **Performance Requirements**: What are your time constraints?
   - **Data Characteristics**: What type of data are you storing?

3. **Use Cases and Tradeoffs**
   - **Arrays**: When you need fast random access
   - **Hash Tables**: When you need fast lookups
   - **Trees**: When you need ordered data and efficient search
   - **Graphs**: When you need to model relationships
   - **Heaps**: When you need priority access

4. **Implementation Considerations**
   - Choose appropriate data types
   - Handle memory management properly
   - Implement proper error handling
   - Consider thread safety if needed

5. **Performance Analysis**
   - Analyze time complexity for operations
   - Consider space complexity
   - Test with realistic data sizes
   - Profile performance in practice

Remember: The right data structure can make your code faster and more efficient."""
    
    def _generate_design_patterns_response(self, prompt: str) -> str:
        """Generate design patterns response"""
        return f"""🏗️ Software Design Patterns

Use design patterns to write better, more maintainable code:

1. **Creational Patterns**
   - **Singleton**: Ensure only one instance of a class
   - **Factory**: Create objects without specifying exact classes
   - **Builder**: Construct complex objects step by step
   - **Prototype**: Create objects by cloning existing ones

2. **Structural Patterns**
   - **Adapter**: Convert interface of one class to another
   - **Decorator**: Add responsibilities to objects dynamically
   - **Facade**: Provide simplified interface to complex system
   - **Composite**: Treat individual objects and compositions uniformly

3. **Behavioral Patterns**
   - **Observer**: Notify multiple objects of state changes
   - **Strategy**: Define family of algorithms, make them interchangeable
   - **Command**: Encapsulate request as object
   - **State**: Allow object to change behavior based on internal state

4. **When to Use Patterns**
   - When you need to solve a common problem
   - When you want to improve code reusability
   - When you need to make code more maintainable
   - When you want to communicate design intent

5. **Pattern Implementation Best Practices**
   - Understand the problem the pattern solves
   - Don't overuse patterns - use them when appropriate
   - Document pattern usage in your code
   - Consider performance implications

Remember: Design patterns are not about implementing specific code, but about solving common design problems in a proven way."""
    
    def _generate_general_programming_response(self, prompt: str) -> str:
        """Generate general programming response"""
        return f"""🎯 General Programming Guidance

Here's some general programming advice:

1. **Fundamental Principles**
   - Write clean, readable code
   - Follow coding standards and conventions
   - Test your code thoroughly
   - Document your code appropriately

2. **Development Process**
   - Plan before coding
   - Write code incrementally
   - Test frequently
   - Refactor when needed

3. **Problem-Solving**
   - Break problems into smaller pieces
   - Use pseudocode to plan solutions
   - Test with various inputs
   - Learn from mistakes

4. **Continuous Learning**
   - Stay updated with new technologies
   - Practice regularly
   - Learn from other developers
   - Teach others to solidify your knowledge

Remember: Programming is both an art and a science. Balance technical skills with creativity and problem-solving."""
    
    def process_programming_query(self, prompt: str) -> Dict:
        """
        Process a programming education query and return appropriate response.
        """
        # Detect programming intent
        intent = self.detect_programming_intent(prompt)
        
        if not intent['is_programming_education']:
            return {
                'success': False,
                'message': 'This is not a programming education query.',
                'intent': intent
            }
        
        # Generate educational response
        response = self.generate_educational_response(prompt, intent['category'])
        
        # Learn from this interaction
        try:
            learn_from_chat(
                prompt=prompt,
                answer=response,
                meta={
                    'source': 'programming_education_system',
                    'category': intent['category'],
                    'confidence': intent['confidence'],
                    'timestamp': datetime.now().isoformat(),
                    'verified': True
                }
            )
        except Exception as e:
            print(f"Warning: Could not learn from interaction: {e}")
        
        return {
            'success': True,
            'message': response,
            'category': intent['category'],
            'confidence': intent['confidence'],
            'archetype': intent['archetype'],
            'intent': intent
        }
    
    def get_programming_categories(self) -> Dict:
        """Get available programming education categories"""
        return self.programming_categories
    
    def get_educational_archetypes(self) -> Dict:
        """Get programming-specific flow archetypes"""
        return self.programming_archetypes


def main():
    """Test the programming education system"""
    print("🎓 Testing Programming Education System...")
    
    # Create the system
    system = ProgrammingEducationSystem()
    
    # Test queries
    test_queries = [
        "How do I approach a new programming problem?",
        "What are the best practices for writing clean code?",
        "How do I learn programming effectively?",
        "How do I refactor my code?",
        "What debugging techniques should I use?",
        "How do I design algorithms?",
        "When should I use different data structures?",
        "What design patterns should I know?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        result = system.process_programming_query(query)
        
        if result['success']:
            print(f"✅ Category: {result['category']}")
            print(f"📊 Confidence: {result['confidence']:.2f}")
            print(f"🎯 Archetype: {result['archetype']}")
            print("\n" + result['message'][:200] + "...")
        else:
            print("❌ No educational content available")
    
    print("\n🎉 Programming Education System test complete!")


if __name__ == "__main__":
    main()