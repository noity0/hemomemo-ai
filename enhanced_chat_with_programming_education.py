"""
🎓 enhanced_chat_with_programming_education.py — ENHANCED CHAT WITH PROGRAMMING EDUCATION
========================================================================================
Enhances Hemomemo AI's chat functionality with programming education capabilities.
Integrates programming education into the existing chat flow.

QANOON: 100% local, no external AI platforms, no FFmpeg, no cloud dependencies.
"""

import os
import sys
import re
import json
from typing import Dict, List, Tuple, Optional

# Add to Hemomemo AI's existing modules
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

def detect_programming_education_intent(prompt: str) -> Dict:
    """
    Detect if the user is asking about programming education.
    Returns intent information if detected, otherwise None.
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
            'all_categories': detected_categories
        }
    else:
        return {
            'is_programming_education': False,
            'category': None,
            'confidence': 0.0,
            'all_categories': {}
        }

def get_programming_education_response(prompt: str, category: str) -> str:
    """
    Generate a programming education response based on the detected category.
    """
    if category == 'thinking':
        return """🧠 Programming Thinking Methodology

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
    
    elif category == 'coding':
        return """💻 Coding Best Practices

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

Remember: Code is read more often than it's written. Write for humans first, computers second."""
    
    elif category == 'learning':
        return """📚 Effective Programming Learning Strategies

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

Remember: Learning to code is a marathon, not a sprint. Consistency beats intensity every time."""
    
    elif category == 'editing':
        return """✏️ Code Editing and Refactoring Techniques

Improve your code with these editing and refactoring strategies:

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

Remember: Refactoring is not about changing functionality, it's about improving code quality while maintaining the same behavior."""
    
    elif category == 'debugging':
        return """🐛 Debugging Techniques and Strategies

Debug effectively with these systematic approaches:

1. **Debugging Mindset**
   - View errors as learning opportunities
   - Be systematic and patient
   - Read error messages carefully - they contain clues
   - Use debugging tools and techniques

2. **Systematic Debugging Process**
   - Reproduce: Create a minimal test case that shows the bug
   - Isolate: Narrow down the code causing the issue
   - Hypothesize: Form a hypothesis about the cause
   - Test: Verify your hypothesis by modifying the code
   - Fix: Implement the solution
   - Verify: Ensure the fix works and doesn't introduce new bugs

3. **Common Debugging Scenarios**
   - Null Reference: Check for uninitialized variables
   - Off-by-One Errors: Verify array/index bounds
   - Logic Errors: Review conditional statements
   - Resource Leaks: Ensure proper cleanup

Remember: Every programmer debugs. The best programmers are the best debuggers."""
    
    elif category == 'algorithms':
        return """🔍 Algorithm Design and Implementation

Design effective algorithms with these principles:

1. **Algorithm Design Process**
   - Understand the problem requirements
   - Choose appropriate data structures
   - Design step-by-step solution
   - Analyze time and space complexity
   - Implement and test thoroughly

2. **Common Algorithm Patterns**
   - Sorting: QuickSort, MergeSort, HeapSort
   - Searching: Binary Search, Depth-First Search, Breadth-First Search
   - Dynamic Programming: Break into overlapping subproblems
   - Greedy Algorithms: Make locally optimal choices
   - Divide and Conquer: Solve smaller instances of the same problem

3. **Complexity Analysis**
   - Time Complexity: O(1), O(log n), O(n), O(n log n), O(n²)
   - Space Complexity: Memory usage analysis
   - Tradeoffs: Balance between time and space

Remember: The best algorithm is often the simplest one that solves the problem correctly."""
    
    elif category == 'design_patterns':
        return """🏗️ Software Design Patterns

Use design patterns to write better, more maintainable code:

1. **Creational Patterns**
   - Singleton: Ensure only one instance of a class
   - Factory: Create objects without specifying exact classes
   - Builder: Construct complex objects step by step
   - Prototype: Create objects by cloning existing ones

2. **Structural Patterns**
   - Adapter: Convert interface of one class to another
   - Decorator: Add responsibilities to objects dynamically
   - Facade: Provide simplified interface to complex system
   - Composite: Treat individual objects and compositions uniformly

3. **Behavioral Patterns**
   - Observer: Notify multiple objects of state changes
   - Strategy: Define family of algorithms, make them interchangeable
   - Command: Encapsulate request as object
   - State: Allow object to change behavior based on internal state

Remember: Design patterns are not about implementing specific code, but about solving common design problems in a proven way."""
    
    else:
        return """🎯 General Programming Guidance

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

Remember: Programming is both an art and a science. Balance technical skills with creativity and problem-solving."""

def enhanced_chat_response(prompt: str, original_response_func, *args, **kwargs) -> Tuple[str, Dict]:
    """
    Enhanced chat response that checks for programming education queries.
    If detected, returns programming education response.
    Otherwise, falls back to original response function.
    """
    # Check if this is a programming education query
    intent = detect_programming_education_intent(prompt)
    
    if intent['is_programming_education'] and intent['confidence'] > 0.5:
        # Generate programming education response
        response = get_programming_education_response(prompt, intent['category'])
        
        # Return response with metadata indicating it's programming education
        metadata = {
            'source': 'programming_education',
            'category': intent['category'],
            'confidence': intent['confidence'],
            'is_programming_education': True
        }
        
        return response, metadata
    else:
        # Fall back to original response function
        return original_response_func(*args, **kwargs)

# Test function
def test_programming_education():
    """Test the programming education detection and response system"""
    test_queries = [
        "How do I approach a new programming problem?",
        "What are the best practices for writing clean code?",
        "How do I learn programming effectively?",
        "How do I refactor my code?",
        "What debugging techniques should I use?",
        "How do I design algorithms?",
        "When should I use different data structures?",
        "What design patterns should I know?",
        "Hello, how are you?",  # Non-programming query
        "Tell me about the weather"  # Non-programming query
    ]
    
    print("🎓 Testing Programming Education System...")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        intent = detect_programming_education_intent(query)
        
        if intent['is_programming_education']:
            print(f"✅ Detected as programming education: {intent['category']}")
            print(f"📊 Confidence: {intent['confidence']:.2f}")
            response = get_programming_education_response(query, intent['category'])
            print(f"📝 Response preview: {response[:100]}...")
        else:
            print("❌ Not detected as programming education")
    
    print("\n🎉 Programming Education System test complete!")

if __name__ == "__main__":
    test_programming_education()