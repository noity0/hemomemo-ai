"""
Debug training system for Hemomemo AI programming education
"""

import os
import sys
import json

# Add to Hemomemo AI's existing modules
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

print(f"Root directory: {ROOT}")
print(f"Python path: {sys.path[:3]}")

# Check if learner module exists
try:
    from model.learner import learn_from_chat, STORE
    print("Learner module imported successfully")
    print(f"Training data file: {STORE}")
    
    # Check if training data file exists
    if os.path.exists(STORE):
        print("Training data file exists")
        with open(STORE, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            print(f"File size: {len(content)} characters")
            print("First few lines:")
            for i, line in enumerate(content.split('\n')[:5]):
                print(f"  {i+1}: {line[:100]}...")
    else:
        print("Training data file does not exist")
        # Create the file
        os.makedirs(os.path.dirname(STORE), exist_ok=True)
        with open(STORE, 'w', encoding='utf-8') as f:
            f.write("# Hemomemo AI training data\n")
        print("Created training data file")
    
    # Test learning with a simple example
    print("\nTesting learning system...")
    result = learn_from_chat(
        prompt="Test prompt",
        answer="Test answer",
        meta={
            'source': 'test',
            'category': 'test',
            'difficulty': 'test',
            'quality': 1.0,
            'timestamp': '2026-01-01T00:00:00',
            'verified': True
        }
    )
    
    if result:
        print("Learning system test successful")
    else:
        print("Learning system test failed")
        
except Exception as e:
    print(f"Error importing learner module: {e}")
    import traceback
    traceback.print_exc()

# Test training data
training_data = [
    {
        "prompt": "What are programming thinking methodologies?",
        "response": "Programming thinking involves computational thinking, systematic approach, debugging mindset, and learning process.",
        "category": "thinking",
        "difficulty": "intermediate",
        "quality": 0.95,
        "source": "qanoon_compliant_training"
    }
]

print(f"\nTraining data examples: {len(training_data)}")
for i, item in enumerate(training_data):
    print(f"  {i+1}. {item['category']} - {item['difficulty']}")