#!/usr/bin/env python3
"""
Simple test for Prompt Understanding System
"""

import sys
import os
sys.path.append('.')
sys.path.append('agent')

from agent.prompt_understanding_interface import PromptUnderstandingInterface

def main():
    print("Testing Prompt Understanding System...")
    print("=" * 50)
    
    # Initialize interface
    interface = PromptUnderstandingInterface()
    
    # Test prompts
    test_prompts = [
        "hello how are you",
        "calculate 2+2",
        "write python code",
        "who are you",
        "what is the meaning of life"
    ]
    
    # Test understanding
    for prompt in test_prompts:
        print(f"\nTesting: {prompt}")
        print("-" * 30)
        
        try:
            # Get intent
            intent = interface.get_intent(prompt)
            print(f"Intent: {intent}")
            
            # Get confidence
            confidence = interface.get_confidence(prompt)
            print(f"Confidence: {confidence:.2f}")
            
            # Get entities
            entities = interface.get_entities(prompt)
            print(f"Entities: {entities}")
            
            # Get domain
            domain = interface.classify_for_domain_routing(prompt)
            print(f"Domain: {domain}")
            
            print("Success")
            
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main()