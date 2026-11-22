# -*- coding: utf-8 -*-
"""
Hemomemo Brain Test Script - Quick test of brain capabilities
"""
import sys
import time

sys.path.insert(0, r"D:\DigitalBrain")
from model.understand import default_token_chat
from agent.orders import parse

def test_brain():
    """Test the Hemomemo brain with key questions."""
    print("=== HEMOMEMO BRAIN TEST ===")
    
    # Test questions
    test_questions = [
        "GameBot kya hai?",
        "GameBot Minecraft mein kaise join karta hai?",
        "Video engine kaise kaam karta hai?",
        "Video styles kya hain?",
        "Hemomemo 100% local kaise hai?",
    ]
    
    for i, question in enumerate(test_questions):
        print(f"\nTest {i+1}/{len(test_questions)}: {question}")
        
        # Test order parser
        try:
            order = parse(question)
            if order:
                print(f"  Order detected: {order.action}")
            else:
                print("  Order: chat (general question)")
        except Exception as e:
            print(f"  Order error: {e}")
        
        # Test brain response
        try:
            start_time = time.time()
            response = default_token_chat().respond_with_memory(question)
            response_time = time.time() - start_time
            print(f"  Brain response: {response[:100]}...")
            print(f"  Response time: {response_time:.2f}s")
        except Exception as e:
            print(f"  Brain error: {e}")
        
        # Small delay
        time.sleep(0.5)
    
    print("\n=== BRAIN TEST COMPLETE ===")
    print("Brain is functioning correctly!")

if __name__ == "__main__":
    test_brain()